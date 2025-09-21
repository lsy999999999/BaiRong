<template>
  <div class="tilemap-container" ref="tilemapRootContainer"></div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, watch, nextTick, computed, watchEffect } from 'vue';
import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import BuildingRenderer from './BuildingRenderer';
import RoadRenderer from './RoadRenderer';
import CharacterRenderer from './CharacterRenderer';
import { useGameStore } from '../../stores/gameStore';
import EventModalProcess from './EventModalProcess';

export default {
  name: 'TilemapRenderer',
  props: {
    mapData: {
      type: Object,
      required: true
    }
  },
  emits: ['map-loaded'],
  setup(props, { emit }) {
    // 使用游戏状态store
    const gameStore = useGameStore();

    // 使用store中的值替代本地变量
    const isPaused = computed(() => gameStore.isPaused);
    const gameSpeed = computed(() => gameStore.gameSpeed);

    const tilemapRootContainer = ref(null);
    // 只保留拖拽状态
    const isDragging = ref(false);
    
    let app = null;
    let viewport = null;
    let groundLayer = null;
    let roadLayer = null;
    let sceneLayer = null;
    let decorationLayer = null;
    let textures = {};
    let finalResult = {};
    let isInitialized = false;
    let buildingRenderer = null;
    let roadRenderer = null;
    let characterRenderer = null;  // 保留人物渲染器
    let animationFrameId = null;  // 用于存储动画帧ID
    let eventModalProcess = null;  // 事件管理器

    // 存储相机控制器方法
    let cameraController = {
      updateCameraFollow: null,
      viewCharacterDetail: null
    };

    window.textures = {};
    window.finalResult = {};
    const padding = 0;

    // 使用gameStore获取isDevMode状态
    const isDevMode = computed(() => gameStore.isDevMode);

    // 初始化代理生成队列
    const agentGenerationQueue = ref([]);

    // 初始化代理生成队列方法
    const initAgentGenerationQueue = () => {
      if (!gameStore) {
        console.error('游戏状态store未初始化');
        return;
      }

      // 获取agents数据
      const agentsData = gameStore.agentsData;
      const systemConfig = gameStore.systemConfig;

      // 检查是否有可用的agents
      if (!agentsData || !agentsData.agents || agentsData.agents.length === 0) {
        console.warn('没有可用的agents数据');
        return;
      }

      // 获取已创建的角色列表
      const createdCharacters = gameStore.characters || [];

      // 从createdCharacters提取已使用的agentId
      const usedAgentIds = new Set(createdCharacters
        .filter(char => char.agentId)
        .map(char => char.agentId));

      // 按照agent类型分组
      const agentGroups = {};
      const agentTypePortraitMap = {};

      // 收集每种类型的portrait映射
      if (systemConfig && systemConfig.agent && systemConfig.agent.profile) {
        Object.keys(systemConfig.agent.profile).forEach(agentType => {
          const agentConfig = systemConfig.agent.profile[agentType];
          if (agentConfig && agentConfig.portrait) {
            agentTypePortraitMap[agentType] = agentConfig.portrait;
          }
        });
      }

      // 按类型分组可用的agents
      agentsData.agents.forEach(agent => {
        // 确保profile和agent_type存在
        if (agent.profile && agent.profile.agent_type) {
          const agentType = agent.profile.agent_type;

          // 初始化分组
          if (!agentGroups[agentType]) {
            agentGroups[agentType] = [];
          }

          // 将未使用的agent添加到对应分组
          if (!usedAgentIds.has(agent.id)) {
            agentGroups[agentType].push(agent);
          }
        }
      });

      // 创建平均分布的队列
      const queue = [];
      const agentTypes = Object.keys(agentGroups).filter(type => agentGroups[type].length > 0);

      // 如果没有可用的agent类型，直接返回
      if (agentTypes.length === 0) {
        console.warn('没有可用的agent类型');
        return;
      }

      // 洗牌每种类型的agents，确保随机性
      agentTypes.forEach(type => {
        agentGroups[type] = shuffleArray([...agentGroups[type]]);
      });

      // 计算最大可能的循环次数
      const maxIterations = Math.max(...agentTypes.map(type => agentGroups[type].length));

      // 轮流从每种类型添加agent到队列，确保均匀分布
      for (let i = 0; i < maxIterations; i++) {
        for (const type of agentTypes) {
          if (i < agentGroups[type].length) {
            const agent = agentGroups[type][i];
            // 将portrait值映射到characterType
            let characterType = "citizen"; // 默认为citizen类型

            if (agentTypePortraitMap[type]) {
              // 将portrait值映射到characterType
              switch (agentTypePortraitMap[type]) {
                case 1:
                  characterType = "government";
                  break;
                case 2:
                  characterType = "researcher";
                  break;
                case 3:
                  characterType = "worker";
                  break;
                case 4:
                  characterType = "merchant";
                  break;
                case 5:
                  characterType = "citizen";
                  break;
                default:
                  characterType = "citizen";
              }
            }

            queue.push({
              agentId: agent.id,
              agentType: characterType,
              profile: agent.profile || {}
            });
          }
        }
      }

      console.log(`初始化代理生成队列完成，共${queue.length}个代理`);
      agentGenerationQueue.value = queue;
    };

    // 洗牌数组的辅助函数
    const shuffleArray = (array) => {
      for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
      }
      return array;
    };

    // 从生成队列中获取下一个agent
    const getAgentMapping = () => {
      // 检查队列是否为空
      if (agentGenerationQueue.value.length === 0) {
        console.warn('生成队列已用尽，无可用agents');
        return { agentId: null, agentType: null, profile: {} };
      }

      // 从队列头部取出一个agent
      const nextAgent = agentGenerationQueue.value.shift();
      // console.log(`从队列获取agent: ID=${nextAgent.agentId}, 类型=${nextAgent.agentType}, 剩余${agentGenerationQueue.value.length}个`,nextAgent.profile);

      return nextAgent;
    };

    // 创建并初始化PIXI应用
    const initPixiApp = async () => {
      if (!tilemapRootContainer.value) return;

      try {
        // 先检查gameStore中是否已有PIXI应用实例
        app = gameStore.getPixiApp;
        
        if (!app) {
          // 如不存在，创建PIXI应用 - 使用v8的API
          app = new PIXI.Application();
          
          // 异步初始化应用
          await app.init({
            width: tilemapRootContainer.value.clientWidth,
            height: tilemapRootContainer.value.clientHeight,
            backgroundColor: 0x87CEEB, // 天蓝色背景
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
            antialias: true,
            // 设置为rootStage可以直接渲染到根stage
            rootStage: true
          });
          
          // 将创建的应用实例保存到gameStore
          gameStore.setPixiApp(app);
        } else {
          // 如已存在，更新尺寸
          app.renderer.resize(
            tilemapRootContainer.value.clientWidth,
            tilemapRootContainer.value.clientHeight
          );
        }

        // 将canvas添加到DOM容器中
        tilemapRootContainer.value.appendChild(app.canvas);

        // 初始化建筑渲染器
        buildingRenderer = new BuildingRenderer();

        // 初始化道路渲染器
        roadRenderer = new RoadRenderer();

        // 初始化人物渲染器
        characterRenderer = new CharacterRenderer();
        // 确保在下一个tick初始化游戏store
        setTimeout(() => {
          if (characterRenderer && characterRenderer.initGameStore) {
            characterRenderer.initGameStore();
            console.log('人物渲染器的游戏状态store已初始化');
          }
        }, 0);

        // 初始化viewport
        initViewport();

        // 开始游戏循环
        startGameLoop();

        // 标记已初始化
        isInitialized = true;
      } catch (error) {
        console.error('初始化PIXI应用时出错:', error);
      }
    };

    // 初始化Viewport（地图相机）
    const initViewport = () => {
      try {
        console.log('初始化视口');

        // 计算地图像素大小
        const worldWidth = props.mapData.width * props.mapData.tileWidth;
        const worldHeight = props.mapData.height * props.mapData.tileHeight;

        console.log(`视口尺寸: ${tilemapRootContainer.value.clientWidth}x${tilemapRootContainer.value.clientHeight}, 世界尺寸: ${worldWidth}x${worldHeight}, Padding: ${padding}px`);

        // 先检查gameStore中是否已有viewport实例
        viewport = gameStore.getViewport;
        
        if (!viewport) {
          viewport = new Viewport({
            screenWidth: tilemapRootContainer.value.clientWidth,
            screenHeight: tilemapRootContainer.value.clientHeight,
            worldWidth: worldWidth + padding * 2, // 增加世界宽度
            worldHeight: worldHeight + padding * 2, // 增加世界高度
            events: app.renderer.events // PIXI.js v8中使用events替代interaction
          });

          app.stage.addChild(viewport);
          
          // 设置Viewport插件
          viewport
            .drag({ wheel: false })
            .pinch()
            .wheel()
            .decelerate();
          
          // 监听拖拽事件
          viewport.on('drag-start', () => {
            isDragging.value = true;
          });
          
          viewport.on('drag-end', () => {
            isDragging.value = false;
          });
          
          // 移除鼠标移动事件监听
          
          // 将创建的viewport实例保存到gameStore
          gameStore.setViewport(viewport);
        } else {
          // 如果已存在，更新尺寸和边界
          viewport.resize(
            tilemapRootContainer.value.clientWidth,
            tilemapRootContainer.value.clientHeight,
            worldWidth + padding * 2,
            worldHeight + padding * 2
          );
          
          // 确保viewport已添加到舞台
          if (!viewport.parent) {
            app.stage.addChild(viewport);
          }
          
          // 确保事件监听器已添加
          if (!viewport._events['drag-start']) {
            viewport.on('drag-start', () => {
              isDragging.value = true;
            });
          }
          
          if (!viewport._events['drag-end']) {
            viewport.on('drag-end', () => {
              isDragging.value = false;
            });
          }
          
          // 移除鼠标移动事件监听
          
        }

        // 设置缩放限制 - 考虑padding后的边界
        viewport.clamp({
          left: -padding,
          right: worldWidth + 2 * padding,
          top: -padding,
          bottom: worldHeight + 2 * padding
        });

        viewport.clampZoom({
          minScale: 0.5,
          maxScale: 2
        });

        // 初始缩放和位置 - 确保能看到地图内容
        const initialScale = 0.5;

        viewport.setZoom(initialScale, true);

        // 移动到地图中心点，考虑padding
        viewport.moveCenter(
          worldWidth / 2 + 2 * padding,
          worldHeight / 2 + 2 * padding
        );

        console.log('视口初始化完成，位置:', viewport.position, '缩放:', viewport.scale);
      } catch (error) {
        console.error('初始化Viewport时出错:', error);
      }
    };

    // 添加一个静态标志，跟踪是否已加载资源包
    let resources = null;
    const loadSpriteSheet = async () => {
      try {
        // 定义需要加载的资源包
        const bundleCount = 3;
        const bundleNames = [];
        const bundleSources = [];
        // 创建animations对象用于存储动画数据
        let animations = {};

        for (let i = 0; i < bundleCount; i++) {
          bundleNames.push(`tilesets_${i}`);
          bundleSources.push({
            [`bgrd_${i}`]: `/assets/bgrd-${i}.json` // 统一使用 public 中的路径，在开发和生产环境中都有效
          });
        }
        console.log('bundleSources:', bundleSources);
        console.log('设置全局默认 alphaMode', PIXI.TextureSource);
        // 循环加载所有资源包
        for (let i = 0; i < bundleCount; i++) {
          const bundleName = bundleNames[i];
          const bundleSource = bundleSources[i];
          const textureKey = Object.keys(bundleSource)[0]; // 获取纹理键名(如bgrd_0)

          console.log(`注册精灵表资源包 ${bundleName}...`);
          PIXI.Assets.addBundle(bundleName, bundleSource);

          console.log(`开始加载精灵表资源 ${bundleName}...`);
          resources = await PIXI.Assets.loadBundle(bundleName);
          console.log(`精灵表资源 ${bundleName} 加载完成:`, resources);

          // 将资源中的纹理添加到textures对象中
          Object.keys(resources[textureKey].textures).forEach(key => {
            textures[key] = resources[textureKey].textures[key];
          });

          // 提取并存储animations数据
          if (resources[textureKey].animations) {
            Object.keys(resources[textureKey].animations).forEach(key => {
              animations[key] = resources[textureKey].animations[key];
            });
          }
        }
        window.textures = textures;
        console.log("textures", textures);

        // 创建全局animations变量
        window.animations = animations;
        console.log('动画数据已加载:', window.animations);
        // 合并纹理到一个对象中
        // console.log('精灵表纹理已加载:', window.textures);
        // 创建统计对象来存储各类资源的风格数量
        const styleCount = {};

        // 遍历所有纹理路径
        Object.keys(textures).forEach(path => {
          const parts = path.split('/');

          // 跳过没有足够路径段的情况
          if (parts.length < 2) return;

          const resourceType = parts[0]; // 如 'house', 'decoration', 'bg' 等

          // 初始化resourceType对应的对象
          if (!styleCount[resourceType]) {
            styleCount[resourceType] = {};
          }

          // 根据不同的资源类型处理
          if (resourceType === 'house') {
            // house类型: house/XX/XX_Y_Z.png
            if (parts.length >= 3) {
              const itemId = parts[1];  // 如 20, 21, 22 等
              const filename = parts[2];
              const filenameParts = filename.split('_');

              // 检查是否至少有两个部分 (XX_Y)
              if (filenameParts.length >= 2) {
                const styleNum = filenameParts[1];  // 第二部分是风格编号

                // 初始化 itemId 对应的对象
                if (!styleCount[resourceType][itemId]) {
                  styleCount[resourceType][itemId] = {};
                }

                // 统计每个风格的数量
                if (!styleCount[resourceType][itemId][styleNum]) {
                  styleCount[resourceType][itemId][styleNum] = 0;
                }

                // 增加该风格的计数
                styleCount[resourceType][itemId][styleNum]++;
              }
            }
          } else if (resourceType === 'decoration' || resourceType === 'villa') {
            // decoration类型: decoration/XX/XX_Y.png
            // villa类型: villa/XX/XX_Y.png
            if (parts.length >= 3) {
              const itemId = parts[1];  // 如 30, 31 等
              const filename = parts[2];
              const filenameParts = filename.split('_');

              // 检查是否至少有两个部分 (XX_Y)
              if (filenameParts.length >= 2) {
                const styleNum = filenameParts[1].split('.')[0];  // 提取Y部分，去掉扩展名

                // 初始化 itemId 对应的对象
                if (!styleCount[resourceType][itemId]) {
                  styleCount[resourceType][itemId] = {};
                }

                // 统计每个风格的数量
                if (!styleCount[resourceType][itemId][styleNum]) {
                  styleCount[resourceType][itemId][styleNum] = 0;
                }

                // 增加该风格的计数
                styleCount[resourceType][itemId][styleNum]++;
              }
            }
          } else if (resourceType === 'bg') {
            // bg类型: bg/type_X.png
            if (parts.length >= 2) {
              const fullname = parts[1]; // 例如 grass_1.png
              const typeWithNum = fullname.split('.')[0]; // 去掉扩展名，得到 grass_1
              const typeParts = typeWithNum.split('_');

              if (typeParts.length >= 2) {
                const typeId = typeParts[0]; // 例如 grass, road
                const styleNum = typeParts[1]; // 风格编号

                // 初始化 typeId 对应的对象
                if (!styleCount[resourceType][typeId]) {
                  styleCount[resourceType][typeId] = {};
                }

                // 统计每个风格的数量
                if (!styleCount[resourceType][typeId][styleNum]) {
                  styleCount[resourceType][typeId][styleNum] = 0;
                }

                // 增加该风格的计数
                styleCount[resourceType][typeId][styleNum]++;
              }
            }
          } else if (resourceType === 'character') {
            // character类型: character/gender/a_b/x.png
            // 例如：character/f/1_1/1.png 等
            if (parts.length >= 4) {
              const gender = parts[1]; // 性别：f或m
              const categoryVariant = parts[2]; // 例如 1_1, 2_1 等
              
              // 确保gender分类存在
              if (!styleCount[resourceType][gender]) {
                styleCount[resourceType][gender] = {};
              }
              
              // 解析a_b格式，提取主类别和次类别
              const variantParts = categoryVariant.split('_');
              if (variantParts.length === 2) {
                const mainCategory = variantParts[0]; // a值，如1, 2, 3
                const subCategory = variantParts[1];  // b值，如1, 2, 3, 4
                
                // 确保主类别在统计中存在
                if (!styleCount[resourceType][gender][mainCategory]) {
                  styleCount[resourceType][gender][mainCategory] = {
                    variants: new Set(), // 用Set记录所有不同的b值
                    fullVariants: {} // 记录完整变体的出现次数
                  };
                }
                
                // 添加次类别到Set中
                styleCount[resourceType][gender][mainCategory].variants.add(subCategory);
                
                // 记录完整变体名称的出现次数
                if (!styleCount[resourceType][gender][mainCategory].fullVariants[categoryVariant]) {
                  styleCount[resourceType][gender][mainCategory].fullVariants[categoryVariant] = 0;
                }
                styleCount[resourceType][gender][mainCategory].fullVariants[categoryVariant]++;
              }
            }
          } else if (resourceType === 'head') {
            // head类型：head/gender/partType/a.png
            // 例如：head/f/e/1.png (女性眼睛1号)
            if (parts.length >= 4) {
              const gender = parts[1]; // 性别：f或m
              const partType = parts[2]; // 部件类型：e(眼睛)、f(脸型)、h(头发)、m(嘴巴)
              const filename = parts[3]; // 文件名，如1.png
              
              // 跳过头发部件(h)中包含下划线的文件(a_b.png)
              if (partType === 'h' && filename.includes('_')) {
                // 不处理这个文件，直接继续下一次循环
              } else {
                // 构建复合键，包含性别和部件类型
                const genderPartType = `${gender}_${partType}`;
                
                // 初始化分类对应的对象
                if (!styleCount[resourceType][genderPartType]) {
                  styleCount[resourceType][genderPartType] = {};
                }
                
                // 从文件名中提取部件编号(去掉扩展名)
                const partNumber = filename.split('.')[0];
                
                // 统计每个部件的数量
                styleCount[resourceType][genderPartType][partNumber] = true;
              }
            }
          }
        });

        // 创建最终结果对象，统计每个类型和ID的风格数量
        finalResult = {};

        // 遍历所有资源类型
        Object.keys(styleCount).forEach(resourceType => {
          if (!finalResult[resourceType]) {
            finalResult[resourceType] = {};
          }

          // 遍历该资源类型下的所有ID
          Object.keys(styleCount[resourceType]).forEach(itemId => {
            // 对于character类型，需要特殊处理
            if (resourceType === 'character') {
              // 对于character类型，我们已经有了每个性别下的所有分类变体
              // itemId此时是gender（f或m）
              const gender = itemId;
              
              // 获取该性别下的所有主分类
              const mainCategories = styleCount[resourceType][gender];
              
              // 确保该性别已初始化在finalResult中
              if (!finalResult[resourceType][gender]) {
                finalResult[resourceType][gender] = {};
              }
              
              // 遍历该性别下的所有主分类
              Object.keys(mainCategories).forEach(mainCategory => {
                // 计算该主分类下有多少个不同的变体(b值)
                const variantCount = mainCategories[mainCategory].variants.size;
                
                // 将结果保存到finalResult中，格式为：{主分类: 变体数量}
                finalResult[resourceType][gender][mainCategory] = variantCount;
              });
            } else if (resourceType === 'head') {
              // 对于head类型，统计每个性别下每种部件的数量
              const [gender, partType] = itemId.split('_');
              
              // 确保gender分类存在
              if (!finalResult[resourceType][gender]) {
                finalResult[resourceType][gender] = {};
              }
              
              // 确保部件类型分类存在
              if (!finalResult[resourceType][gender][partType]) {
                finalResult[resourceType][gender][partType] = 0;
              }
              
              // 统计该部件类型的数量
              const partCount = Object.keys(styleCount[resourceType][itemId]).length;
              finalResult[resourceType][gender][partType] = partCount;
            } else {
              // 其他资源类型，统计每个ID有多少种风格
              finalResult[resourceType][itemId] = Object.keys(styleCount[resourceType][itemId]).length;
            }
          });
        });
        window.finalResult = finalResult;
        console.log('资源风格统计结果:', finalResult);
        return resources;
      } catch (error) {
        console.warn('加载精灵表失败:', error);
        throw error;
      }
    };
    // 渲染地图
    const renderMap = () => {
      if (!app || !viewport) {
        console.error('应用或视口未初始化，无法渲染地图');
        return;
      }

      try {
        console.log('开始渲染地图');
        const { width, height, tileWidth, tileHeight, layers } = props.mapData;
        console.log(`地图尺寸: ${width}x${height}, 瓦片尺寸: ${tileWidth}x${tileHeight}`);

        // 清理旧图层
        if (groundLayer) {
          viewport.removeChild(groundLayer);
          groundLayer.destroy();
        }

        if (roadLayer) {
          viewport.removeChild(roadLayer);
          roadLayer.destroy();
        }

        if (sceneLayer) {
          viewport.removeChild(sceneLayer);
          sceneLayer.destroy();
        }

        if (decorationLayer) {
          viewport.removeChild(decorationLayer);
          decorationLayer.destroy();
        }

        if (sceneLayer) {
          viewport.removeChild(sceneLayer);
          sceneLayer.destroy();
        }

        // 创建图层容器
        groundLayer = new PIXI.Container();
        roadLayer = new PIXI.Container();
        sceneLayer = new PIXI.Container();
        decorationLayer = new PIXI.Container();

        // 启用场景层的sortableChildren属性以支持zIndex排序
        sceneLayer.sortableChildren = true;

        // 添加偏移量以考虑padding
        groundLayer.position.set(padding, padding);
        roadLayer.position.set(padding, padding);
        sceneLayer.position.set(padding, padding);
        decorationLayer.position.set(padding, padding);

        // 按照渲染顺序添加到视口
        viewport.addChild(groundLayer);    // 底层：地面
        viewport.addChild(decorationLayer); // 第二层：装饰物
        viewport.addChild(roadLayer);      // 第三层：道路
        viewport.addChild(sceneLayer);  // 第四层：建筑


        // 渲染地面层（第一层）
        const groundData = layers[0].data;
        console.log('渲染地面层, 数据长度:', groundData);

        // 调试查看地面层数据中的瓦片ID
        const groundTileIds = new Set(groundData.filter(id => id !== 0));
        console.log('地面层中的瓦片ID:', [...groundTileIds]);

        let groundTileCount = 0;
        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            const tileId = groundData[y * width + x].toString(); // 确保转换为字符串ID

            // 使用bgrd中的背景纹理
            // 根据tileId选择不同的背景纹理
            let bgTextureName;

            if (tileId === '1') {
              bgTextureName = 'bg/grass_1.png';
            } else if (tileId === '2') {
              // 当tileId为2时，使用bg_03.png
              bgTextureName = 'bg/grass_2.png';
            } else {
              // 默认使用bg_01.png
              bgTextureName = 'bg/grass_1.png';
            }

            if (window.textures[bgTextureName]) {
              // 创建精灵
              const sprite = new PIXI.Sprite(window.textures[bgTextureName]);

              // 四舍五入到整数位置，并应用负补偿以消除间隙
              sprite.x = Math.floor(x * tileWidth);
              sprite.y = Math.floor(y * tileHeight);
              sprite.width = tileWidth + 1;  // 增加1像素宽度，避免间隙
              sprite.height = tileHeight + 1; // 增加1像素高度，避免间隙

              groundLayer.addChild(sprite);
              groundTileCount++;
            }
          }
        }
        console.log(`地面层渲染完成，放置了 ${groundTileCount} 个瓦片`);

        // 使用RoadRenderer渲染道路层（第二层）
        renderRoadLayer();

        // 使用BuildingRenderer渲染建筑层（第三层）
        rendersceneLayer();

        // 使用renderDecorationLayer渲染建筑层（第三层）
        renderDecorationLayer();
        // 检查是否有瓦片被成功渲染
        if (groundTileCount === 0 && decorationTileCount === 0) {
          console.warn('没有任何瓦片被渲染，可能是地图数据或纹理有问题');
        }

        // 通知地图加载完成
        console.log('地图渲染完成，发出map-loaded事件');
        emit('map-loaded');
      } catch (error) {
        console.error('渲染地图时出错:', error);
      }
    };

    // 渲染道路层（第二层）- 使用RoadRenderer
    const renderRoadLayer = () => {
      const { width, height, tileWidth, tileHeight, layers } = props.mapData;
      const roadData = layers[1].data;
      console.log('渲染道路层, 数据长度:', roadData.length);

      const roadTileIds = new Set(roadData.filter(id => id !== 0));
      console.log('道路层中的瓦片ID:', [...roadTileIds]);

      let roadTileCount = 0;
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const tileId = roadData[y * width + x].toString(); // 确保转换为字符串ID
          if (tileId !== '0') {
            // 根据tileId选择对应的道路纹理
            let roadTextureName = 'road_01.png'; // 默认纹理

            // 根据tileId判断使用哪个道路纹理
            if (tileId === '4') {
              roadTextureName = 'bg/road_02.png'; // tileId为4时使用第1个道路纹理
            } else if (tileId === '5') {
              roadTextureName = 'bg/road_03.png'; // tileId为5时使用第2个道路纹理
            } else if (tileId === '6') {
              roadTextureName = 'bg/road_01.png'; // tileId为6时使用第0个道路纹理
            }

            const roadTextures = window.textures[roadTextureName];

            if (roadTextures) {
              // 创建道路精灵
              const sprite = new PIXI.Sprite(roadTextures);

              // 确保四舍五入到整数位置，防止浮点数舍入误差导致的间隙
              sprite.x = Math.floor(x * tileWidth);
              sprite.y = Math.floor(y * tileHeight);
              // 增加额外的像素确保瓦片之间完全无缝连接
              sprite.width = tileWidth + 1;
              sprite.height = tileHeight + 1;

              // 存储道路节点的网格坐标，便于后续处理
              sprite.roadGridX = x;
              sprite.roadGridY = y;

              roadLayer.addChild(sprite);
              roadTileCount++;
            }
          }
        }
      }
      console.log(`道路层渲染完成，放置了 ${roadTileCount} 个瓦片`);

      // 分析道路网络并保存导航图
      analyzeRoadNetwork();
    };

    /**
     * 分析道路网络并构建导航图
     */
    const analyzeRoadNetwork = () => {
      if (!roadRenderer || !props.mapData) return;

      const { width, height, layers } = props.mapData;
      const roadData = layers[1].data;

      // 调用RoadRenderer分析道路网络
      const navigationGraph = roadRenderer.analyzeRoadNetwork(roadData, width, height);

      // 将导航图保存到全局变量，供其他组件使用
      window.roadNavigationGraph = navigationGraph;

      console.log('道路导航图已生成并保存为全局变量 window.roadNavigationGraph');
      console.log(`导航图包含 ${Object.keys(navigationGraph.nodes).length} 个节点, ${navigationGraph.segments.length} 条道路段`);
    };

    // 渲染建筑层（第三层）
    const rendersceneLayer = () => {
      const { tileWidth, tileHeight } = props.mapData;
      console.log('渲染建筑层, 数据长度:', props.mapData.buildingData);

      // 清理之前的建筑数据
      buildingRenderer.clearTextures();
      
      // 创建一个新数组用于收集建筑精灵数据
      const buildingSpritesData = [];
      
      // 创建一个新数组用于存储到gameStore
      const buildingsForStore = [];

      // 存储已处理过的建筑坐标，避免重复创建
      const processedCoordinates = new Set();

      // 用于存储所有建筑的网格位置到ID的映射
      const gridToBuildingMap = new Map();

      let buildingTileCount = 0;

      // 检查是否有预先计算的建筑数据
      if (props.mapData.buildingData && props.mapData.buildingData.length > 0) {
        console.log(`使用预先计算的建筑数据创建建筑，共 ${props.mapData.buildingData.length} 个建筑`);

        // 使用预先计算的建筑数据创建建筑
        for (const buildingInfo of props.mapData.buildingData) {
          const { x, y, width, height } = buildingInfo;
          // 跳过已处理的坐标
          if (processedCoordinates.has(`${x},${y}`)) continue;

          // 使用BuildingRenderer的createBuilding方法创建建筑
          const result = buildingRenderer.createBuilding(
            buildingInfo,
            tileWidth,
            tileHeight,
            addCharacterIndoor
          );
          // 解构返回值获取建筑精灵、ID和阴影
          const { sprite, buildingId, shadow } = result;
          if (buildingInfo.style === "house") {
            // 保存原来的事件处理器
            const originalOnMouseEnter = sprite.onmouseenter;
            const originalOnMouseLeave = sprite.onmouseleave;

            // 创建新的事件处理器，调用原来的处理器并添加新功能
            sprite.onmouseenter = (event) => {
              // 先调用原来的事件处理器
              if (originalOnMouseEnter) {
                originalOnMouseEnter(event);
              }
            }

            sprite.onmouseleave = (event) => {
              // 先调用原来的事件处理器
              if (originalOnMouseLeave) {
                originalOnMouseLeave(event);
              }
            }
          }
          // 存储网格与建筑ID的映射
          for (let dy = 0; dy < height; dy++) {
            for (let dx = 0; dx < width; dx++) {
              const gridX = x + dx;
              const gridY = y + dy;
              gridToBuildingMap.set(`${gridX},${gridY}`, buildingId);
            }
          }

          // 如果有阴影，添加到场景
          if (shadow) {
            sceneLayer.addChild(shadow);
          }

          // 收集建筑数据到数组中
          const buildingSpriteData = {
            ...buildingInfo,
            buildingId,
            spriteId: sprite.uid
          };
          buildingSpritesData.push(buildingSpriteData);
          
          // 创建完整的建筑对象添加到gameStore数组
          const buildingForStore = {
            ...buildingInfo,
            buildingId,
            spriteId: sprite.uid,
            sprite,
            shadow,
            // 添加其他有用的属性
            occupiedTiles: [],
            indoorCharacters: [],
            isHighlighted: false
          };
          
          // 收集该建筑占用的所有格子
          for (let dy = 0; dy < height; dy++) {
            for (let dx = 0; dx < width; dx++) {
              const gridX = x + dx;
              const gridY = y + dy;
              buildingForStore.occupiedTiles.push({x: gridX, y: gridY});
            }
          }
          
          // 添加到建筑数组
          buildingsForStore.push(buildingForStore);

          // 添加建筑精灵到场景
          sceneLayer.addChild(sprite);
          buildingTileCount++;

          // 标记所有属于这个建筑的格子为已处理
          for (let dy = 0; dy < height; dy++) {
            for (let dx = 0; dx < width; dx++) {
              if (x + dx < props.mapData.width && y + dy < props.mapData.height) {
                processedCoordinates.add(`${x + dx},${y + dy}`);
              }
            }
          }
        }
      }

      // 将网格到建筑ID的映射保存到全局变量，以便其他组件使用
      window.gridToBuildingMap = gridToBuildingMap;

      // 将网格到建筑ID的映射保存到gameStore中，以便其他组件使用
      gameStore.setBuildingData(gridToBuildingMap);
      
      // 将收集的建筑精灵数据保存到gameStore
      gameStore.setBuildingOriginalData(buildingSpritesData);
      
      // 将完整的建筑对象数组保存到gameStore
      gameStore.setBuildings(buildingsForStore);
      
      console.log(`建筑层渲染完成，放置了 ${buildingTileCount} 个建筑`);

      // 对建筑进行排序以确保正确的深度渲染
      // 根据y坐标排序，y值大的(更靠近屏幕底部)显示在前面
      sceneLayer.sortChildren();
      console.log('建筑层渲染完成',sceneLayer);
    };

    //渲染装饰层(第四层)
    const renderDecorationLayer = () => {
      const { width, height, tileWidth, tileHeight, layers } = props.mapData;
      const decorationData = props.mapData.decorationData;
      let decorationTileCount = 0;

      // 创建全局的装饰物格子集合，供CharacterRenderer使用
      window.decorationTiles = new Set();

      if (decorationData && decorationData.length > 0) {
        console.log(`使用预先计算的装饰数据创建建筑，共 ${decorationData.length} 个建筑`);
        for (const decorationInfo of decorationData) {
          const { x, y, type, width, height } = decorationInfo;
          // 根据建筑类型获取可用的风格数量，默认为3种风格
          const styleOptions = finalResult['decoration'] && finalResult['decoration'][type] ? finalResult['decoration'][type] : 3;
          // 随机选择一种风格 (1到styleOptions之间的整数)
          const style = Math.floor(Math.random() * styleOptions) + 1;
          const texture = window.textures[`decoration/${type}/${type}_${style}.png`];
          const sprite = new PIXI.Sprite(texture);

          // 获取贴图的原始尺寸并保持不变
          sprite.width = texture.orig.width;
          sprite.height = texture.orig.height;

          // 计算精灵在网格中的理论尺寸
          const gridWidth = width * tileWidth;
          const gridHeight = height * tileHeight;

          // 计算水平垂直居中的偏移量
          const offsetX = (gridWidth - sprite.width) / 2;
          const offsetY = (gridHeight - sprite.height) / 2;

          // 将精灵位置设置为网格位置加上居中偏移
          sprite.x = Math.floor(x * tileWidth) + offsetX;
          sprite.y = Math.floor(y * tileHeight) + offsetY;
          sprite.zIndex = sprite.y / 2;
          // if (type === 41 || type === 43 || type === 45 || type === 44) {
          //   sprite.zIndex = y * tileHeight;
          // } else {
          //   sprite.zIndex = y * tileHeight + sprite.height; // 修改为使用底部Y坐标作为zIndex
          // }
          // console.log('sprite.zIndex', sprite.x, sprite.y, sprite.zIndex);


          // // 创建装饰物阴影的函数
          // const createDecorationShadow = (sprite, type) => {


          //   // 克隆原精灵来创建阴影
          //   const shadow = new PIXI.Sprite(sprite.texture);

          //   // 复制原精灵的尺寸
          //   shadow.width = sprite.width;
          //   shadow.height = sprite.height;

          //   // 创建颜色过滤器，将精灵变为黑色
          //   const colorMatrix = new PIXI.ColorMatrixFilter();
          //   colorMatrix.blackAndWhite(true); // 先转为黑白
          //   colorMatrix.brightness(0, false); // 再降低亮度，变成黑色

          //   // 应用过滤器
          //   shadow.filters = [colorMatrix];

          //   // 设置透明度
          //   shadow.alpha = 0.4;
          //   if (type !== 44) {
          //     // 设置旋转角度为90度，使阴影水平
          //     // shadow.rotation = 0.25;
          //     // 设置阴影位置，模拟左上方光源
          //     // 阴影位于建筑右侧
          //     shadow.x = sprite.x + 0.05 * sprite.width;
          //     shadow.y = sprite.y;

          //   } else {
          //     shadow.rotation = 0;
          //     shadow.x = sprite.x + 0.1 * sprite.width;
          //     shadow.y = sprite.y;
          //   }
          //   shadow.zIndex = sprite.y;
          //   return shadow;
          // };
          // 创建并添加阴影
          // if (type === 40 || type === 42 || type === 44) {
          //   const shadow = createDecorationShadow(sprite, type);
          //   sceneLayer.addChild(shadow);
          // }
          sceneLayer.addChild(sprite);
          decorationTileCount++;

          // 将装饰物的所有格子添加到全局集合中
          for (let dy = 0; dy < height; dy++) {
            for (let dx = 0; dx < width; dx++) {
              window.decorationTiles.add(`${x + dx},${y + dy}`);
            }
          }
        }
      };
      console.log(`装饰层渲染完成，放置了 ${decorationTileCount} 个瓦片，覆盖了 ${window.decorationTiles.size} 个格子`);
    };

    // 监听窗口大小变化
    const handleResize = () => {
      if (!app || !viewport || !tilemapRootContainer.value) return;

      const width = tilemapRootContainer.value.clientWidth;
      const height = tilemapRootContainer.value.clientHeight;

      app.renderer.resize(width, height);
      viewport.resize(width, height);
    };

    // 清理资源
    const dispose = () => {
      // 停止游戏循环
      stopGameLoop();
      
      // 清理viewport事件监听器
      if (viewport) {
        viewport.off('drag-start');
        viewport.off('drag-end');
      }

    };

    // 监听mapData变化
    watch(() => props.mapData, async (newMapData) => {
      if (!newMapData) return;

      try {
        // 如果已初始化，则清理旧资源
        if (isInitialized) {
          // 不要完全dispose，而是只清理图层资源
          // dispose(); // 不要调用dispose，它会销毁app和viewport

          // 只清理图层
          clearLayers();

          // 初始化代理生成队列
          initAgentGenerationQueue();

          // 确保在DOM准备好后继续
          await nextTick();

          // 如果app或viewport为null，则重新初始化
          if (!app || !viewport) {
            console.log('应用或视口被销毁，重新初始化');
            await initPixiApp();
          } else {
            // 如果viewport存在，更新其边界以适应新的地图尺寸
            const worldWidth = newMapData.width * newMapData.tileWidth;
            const worldHeight = newMapData.height * newMapData.tileHeight;

            console.log(`更新视口边界 - 世界尺寸: ${worldWidth}x${worldHeight}, Padding: ${padding}px`);

            // 更新viewport的世界尺寸
            viewport.resize(
              tilemapRootContainer.value.clientWidth,
              tilemapRootContainer.value.clientHeight,
              worldWidth + padding * 2,
              worldHeight + padding * 2
            );

            // 重新设置边界限制
            viewport.clamp({
              left: -padding,
              right: worldWidth + padding,
              top: -padding,
              bottom: worldHeight + padding
            });

            // 确保视图在地图范围内
            const centerX = worldWidth / 2;
            const centerY = worldHeight / 2;
            viewport.moveCenter(centerX, centerY);
          }

          // 加载贴图并渲染地图
          await loadSpriteSheet();
          renderMap();
          addCharacterOutSide();
          // 生成所有室内人物
          generateAllIndoorCharacters();
          // 地图更新完成后重新启动游戏循环
          startGameLoop();
        } else {
          // 首次初始化，完整设置
          await nextTick();
          await initPixiApp();
          await loadSpriteSheet();
          renderMap();
          addCharacterOutSide();
          // 首次加载完成后启动游戏循环
          startGameLoop();
        }
      } catch (error) {
        console.error('处理mapData变化时出错:', error);
      }
    }, { deep: true });

    // 添加清理图层的方法，不销毁PIXI应用和视口
    const clearLayers = () => {
      // 停止游戏循环
      stopGameLoop();

      // 重置人口计数
      gameStore.resetPopulationCreated();

      // 清理图层
      if (groundLayer && viewport) {
        viewport.removeChild(groundLayer);
        groundLayer.destroy();
        groundLayer = null;
      }

      if (roadLayer && viewport) {
        viewport.removeChild(roadLayer);
        roadLayer.destroy();
        roadLayer = null;
      }

      if (sceneLayer && viewport) {
        viewport.removeChild(sceneLayer);
        sceneLayer.destroy();
        sceneLayer = null;
      }

      if (decorationLayer && viewport) {
        viewport.removeChild(decorationLayer);
        decorationLayer.destroy();
        decorationLayer = null;
      }

      // 重置建筑渲染器
      if (buildingRenderer) {
        buildingRenderer.clearTextures();
      }

      // 重置道路渲染器
      if (roadRenderer) {
        roadRenderer.clearTextures();
      }

      // 清理人物渲染器中的人物
      if (characterRenderer) {
        characterRenderer.clearCharacters();
      }

      // 卸载纹理资源，但不销毁应用实例
      if (textures) {
        try {
          if (typeof PIXI.Assets.unloadBundle === 'function') {
            PIXI.Assets.unloadBundle('tilesets').catch(error => {
              console.warn('卸载精灵表资源失败:', error);
            });
          }
        } catch (error) {
          console.warn('卸载纹理时出错:', error);
        }
        textures = {};
      }
    };

    // 组件挂载时初始化
    onMounted(async () => {
      try {
        // 创建必要的组件实例
        buildingRenderer = new BuildingRenderer();
        roadRenderer = new RoadRenderer();
        characterRenderer = new CharacterRenderer();
        eventModalProcess = new EventModalProcess();

        if (props.mapData) {
          console.log('组件挂载，开始初始化');
          // 确保DOM已经准备好
          await nextTick();
          console.log('DOM已准备好，开始初始化PIXI应用');
          await initPixiApp();
          console.log('PIXI应用初始化完成，开始加载精灵表');
          await loadSpriteSheet();
          console.log('纹理加载完成，开始渲染地图');
          renderMap();

          // 初始化代理生成队列
          initAgentGenerationQueue();
          // 添加角色
          console.log('开始生成角色');
          addCharacterOutSide();
          generateAllIndoorCharacters();
          // 启动游戏循环
          startGameLoop();
          console.log('建筑数据已保存到gameStore', window.gridToBuildingMap);
        }

        // 监听窗口大小变化
        window.addEventListener('resize', handleResize);

        // 确保初始化gameStore的devMode
        gameStore.initDevMode();


      } catch (error) {
        console.error('组件挂载时初始化出错:', error);
      }
    });

    // 组件卸载前清理资源
    onBeforeUnmount(() => {
      dispose();
      window.removeEventListener('resize', handleResize);
    });

    // 添加人物游戏循环
    const startGameLoop = () => {
      let lastTime = Date.now();

      const gameLoop = () => {
        // if(gameStore.isPaused === true){
        //   return;
        // }
        const currentTime = Date.now();
        const deltaTime = (currentTime - lastTime) / 1000;
        lastTime = currentTime;

        // 游戏暂停时不更新，鼠标拖拽视口时也不更新（移除鼠标移动条件）
        if (!isPaused.value && !isDragging.value && characterRenderer && props.mapData) {
          // 应用速度倍率
          const scaledDelta = deltaTime * gameSpeed.value;
          // 更新所有人物
          characterRenderer.updateCharacters(
            scaledDelta,
            props.mapData.tileWidth,
            props.mapData.tileHeight,
            props.mapData.width,
            props.mapData.height,
            window.roadNavigationGraph
          );

          // 实时更新人物精灵的zIndex为它们的y坐标值
          if (gameStore.characters && gameStore.characters.length > 0) {
            for (const character of gameStore.characters) {
              if (character.sprite) {
                // 更新zIndex为网格y坐标，确保人物在y坐标大的位置会显示在前面
                character.sprite.zIndex = character.y || character.gridY;
              }
            }

            // 如果sceneLayer支持sortableChildren，确保开启并排序
            if (sceneLayer && sceneLayer.sortableChildren !== undefined) {
              sceneLayer.sortableChildren = true;
              sceneLayer.sortChildren();
            }
          }
        }
        // 更新镜头跟随
        if (gameStore.getFocusedCharacterId && gameStore.getCameraController.updateCameraFollow) {
          gameStore.getCameraController.updateCameraFollow();
        }
        // 继续下一帧
        animationFrameId = requestAnimationFrame(gameLoop);
      };

      // 启动游戏循环
      animationFrameId = requestAnimationFrame(gameLoop);
    };

    // 停止游戏循环
    const stopGameLoop = () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
    };


    //添加人物
    const addCharacter = (populationSize = 1) => {
      if (!isInitialized || !characterRenderer || !props.mapData) {
        console.error('未初始化，无法添加人物');
        return;
      }
      const { width, height, tileWidth, tileHeight } = props.mapData;

      // 检查是否还有可生成的人口容量
      const remainingCapacity = gameStore.remainingPopulation;

      if (remainingCapacity <= 0) {
        console.warn(`已达到最大人口容量${gameStore.populationCreated}，无法生成更多人物`);
        return;
      }

      // 调整实际生成的人数，不超过剩余容量
      const maxPopulationSize = Math.min(populationSize, remainingCapacity);

      // 用于记录实际创建的角色数量
      let createdCount = 0;

      // 添加指定数量的人物
      for (let i = 0; i < maxPopulationSize; i++) {
        // 获取agent映射关系
        const { agentId, agentType, profile } = getAgentMapping();

        // 如果没有可用的agent，停止创建
        if (!agentId) {
          console.warn('无可用agents，停止创建角色');
          break;
        }

        // 随机选择一个不在建筑物上的位置
        let gridX, gridY;
        let attempts = 0;
        const maxAttempts = 100;
        let gridKey; // 在循环外部定义gridKey变量
        let isInEdgeZone = false;

        do {
          gridX = Math.floor(Math.random() * width);
          gridY = Math.floor(Math.random() * height);
          attempts++;

          // 如果尝试次数过多，跳出循环防止无限循环
          if (attempts > maxAttempts) {
            console.warn('找不到合适的位置放置人物，放弃');
            return;
          }

          // 检查位置是否在建筑物上
          gridKey = `${gridX},${gridY}`; // 对gridKey赋值，而不是重新定义

          // 检查位置是否在边缘区域(EMPTY_5)
          const tileIndex = gridY * width + gridX;
          isInEdgeZone = props.mapData && props.mapData.zoneLayer &&
            props.mapData.zoneLayer[tileIndex] === 104; // 104是TILE_TYPES.EMPTY_5的值

        } while (window.gridToBuildingMap.has(gridKey) || isInEdgeZone);

        // 计算世界坐标
        const x = gridX * tileWidth;
        const y = gridY * tileHeight;

        // 创建人物精灵，传入agentId和agentType以及profile
        const sprite = characterRenderer.createCharacter({
          x, y, gridX, gridY, tileWidth, tileHeight,
          app, mapWidth: width, mapHeight: height,
          agentId, agentType, profile
        });
        sprite.interactive = true;
        sprite.buttonMode = true;
        // 添加点击事件
        sprite.on('click', (event) => {
          const cameraCtrl = gameStore.getCameraController;
          if (cameraCtrl && cameraCtrl.viewCharacterDetail) {
            cameraCtrl.viewCharacterDetail(sprite.agentId, event);
          } else {
            console.warn('相机控制器未初始化，无法查看角色详情');
          }
        });

        sprite.on('mouseover', (event) => {
          // 找到对应的角色数据并暂停移动
          const character = gameStore.characters.find(char => 
            (char.id === sprite.agentId || char.agentId === sprite.agentId)
          );
          
          if (character) {
            character.isPausedByHover = true;
            // 停止动画
            if (character.animatedSprite && character.animatedSprite.playing) {
              character.animatedSprite.stop();
              character.animatedSprite.gotoAndStop(0);
            }
          }
        });
        
        sprite.on('mouseout', (event) => {
          // 找到对应的角色数据并恢复移动
          const character = gameStore.characters.find(char => 
            (char.id === sprite.agentId || char.agentId === sprite.agentId)
          );
          
          if (character) {
            character.isPausedByHover = false;
            // 如果角色正在移动状态，重启动画
            if (character.isMoving && character.animatedSprite && !character.animatedSprite.playing) {
              character.animatedSprite.play();
            }
          }
        });

        // 添加到人物图层
        sceneLayer.addChild(sprite);

        // 增加创建计数
        createdCount++;
      }

      // 更新已创建人口数量，使用实际创建的数量
      gameStore.addPopulationCreated(createdCount);
    };

    // 添加人物到地图
    const addCharacterOutSide = (populationSize = 1) => {
      if (!isInitialized || !characterRenderer || !props.mapData) {
        console.error('未初始化，无法添加人物');
        return;
      }
      const { width, height, tileWidth, tileHeight } = props.mapData;
      populationSize = Math.floor((width - 12) * (height - 12) / 10);
      console.log('室外人物容量', populationSize);
      // 检查是否还有可生成的人口容量
      const remainingCapacity = gameStore.remainingPopulation;

      if (remainingCapacity <= 0) {
        console.warn(`已达到最大人口容量${gameStore.populationCreated}，无法生成更多人物`);
        return;
      }

      // 调整实际生成的人数，不超过剩余容量
      const maxPopulationSize = Math.min(populationSize, remainingCapacity);

      // 用于记录实际创建的角色数量
      let createdCount = 0;

      // 添加指定数量的人物
      for (let i = 0; i < maxPopulationSize; i++) {
        // 获取agent映射关系
        const { agentId, agentType, profile } = getAgentMapping();
        // console.log('添加室外人物', agentId, agentType);
        // 如果没有可用的agent，停止创建
        if (!agentId) {
          console.warn('无可用agents，停止创建角色');
          break;
        }

        // 随机选择一个符合条件的位置：在道路上且不在边缘区域
        let gridX, gridY;
        let attempts = 0;
        const maxAttempts = 300; // 增加尝试次数，因为条件更严格了
        let gridKey;
        let isInEdgeZone = false;
        let isOnRoad = false;

        do {
          gridX = Math.floor(Math.random() * width);
          gridY = Math.floor(Math.random() * height);
          attempts++;

          // 如果尝试次数过多，跳出循环防止无限循环
          if (attempts > maxAttempts) {
            console.warn('找不到合适的道路位置放置人物，放弃');
            return;
          }

          // 检查位置是否在建筑物上
          gridKey = `${gridX},${gridY}`;

          // 检查位置是否在边缘区域(EMPTY_5)
          const tileIndex = gridY * width + gridX;
          isInEdgeZone = props.mapData && props.mapData.zoneLayer &&
            props.mapData.zoneLayer[tileIndex] === 104; // 104是TILE_TYPES.EMPTY_5的值

          // 检查位置是否在道路上
          isOnRoad = window.roadNavigationGraph && 
                     window.roadNavigationGraph.nodes && 
                     window.roadNavigationGraph.nodes[`${gridX}_${gridY}`] !== undefined;

        } while (window.gridToBuildingMap.has(gridKey) || isInEdgeZone || !isOnRoad);

        // 计算世界坐标
        const x = gridX * tileWidth;
        const y = gridY * tileHeight;

        // 创建人物精灵，传入agentId、agentType和profile
        const sprite = characterRenderer.createCharacter({
          x, y, gridX, gridY, tileWidth, tileHeight,
          app, mapWidth: width, mapHeight: height,
          agentId, agentType, profile
        });
        sprite.interactive = true;
        sprite.buttonMode = true;
        // 添加点击事件
        sprite.on('click', (event) => {
          const cameraCtrl = gameStore.getCameraController;
          if (cameraCtrl && cameraCtrl.viewCharacterDetail) {
            cameraCtrl.viewCharacterDetail(sprite.agentId, event);
          } else {
            console.warn('相机控制器未初始化，无法查看角色详情');
          }
        });

                 sprite.on('mouseover', (event) => {
           // 找到对应的角色数据并暂停移动
           const character = gameStore.characters.find(char => 
             (char.id === sprite.agentId || char.agentId === sprite.agentId)
           );
           
           if (character) {
             character.isPausedByHover = true;
             // 停止动画
             if (character.animatedSprite && character.animatedSprite.playing) {
               character.animatedSprite.stop();
               character.animatedSprite.gotoAndStop(0);
             }
           }
         });
         
         sprite.on('mouseout', (event) => {
           // 找到对应的角色数据并恢复移动
           const character = gameStore.characters.find(char => 
             (char.id === sprite.agentId || char.agentId === sprite.agentId)
           );
           
           if (character) {
             character.isPausedByHover = false;
             // 如果角色正在移动状态，重启动画
             if (character.isMoving && character.animatedSprite && !character.animatedSprite.playing) {
               character.animatedSprite.play();
             }
           }
         });

        // 添加到人物图层
        sceneLayer.addChild(sprite);

        // 增加创建计数
        createdCount++;
      }

      // 更新已创建人口数量，使用实际创建的数量
      gameStore.addPopulationCreated(createdCount);
      
      // 更新室外人物总数
      gameStore.populationOutdoor = (gameStore.populationOutdoor || 0) + createdCount;
    };

    // 添加室内人物的方法
    const addCharacterIndoor = (parentSprite) => {
      // console.log('addIndoorCharacter被调用', parentSprite);

      if (!characterRenderer || !props.mapData) {
        console.error('未初始化，无法添加室内人物');
        return null;
      }

      // 检查是否还有可生成的人口容量
      const remainingCapacity = gameStore.remainingPopulation;

      if (remainingCapacity <= 0) {
        console.warn(`已达到最大人口容量${gameStore.populationCreated}，无法生成更多室内人物`);
        return null;
      }

      // 获取agent映射关系
      const { agentId, agentType, profile } = getAgentMapping();
      // console.log('添加室内人物', agentId, agentType);
      // 如果没有可用的agent，停止创建
      if (!agentId) {
        console.warn('无可用agents，停止创建室内角色');
        return null;
      }

      // 获取父精灵的宽度和高度
      const { tileWidth, tileHeight } = props.mapData;
      
      // 如果存在室内地板，使用室内地板的尺寸，否则使用父精灵的尺寸
      const targetSprite = parentSprite.room || parentSprite;
      const spriteWidth = targetSprite.width;
      const spriteHeight = targetSprite.height;

      // 在精灵内随机位置
      const relativeX = Math.random() * (spriteWidth * 0.8) + spriteWidth * 0.1; // 避免太靠边缘
      const relativeY = Math.random() * (spriteHeight * 0.6) + spriteHeight * 0.2; // 避免太靠上下

      // 创建室内人物精灵，传入agentId、agentType和profile
      const indoorSprite = characterRenderer.createIndoorCharacter({
        x: relativeX,
        y: relativeY,
        tileWidth,
        tileHeight,
        app,
        parentSprite: targetSprite, // 使用目标精灵（room或parentSprite）
        bounds: {
          minX: spriteWidth * 0.1,
          maxX: spriteWidth * 0.9,
          minY: spriteHeight * 0.5,
          maxY: spriteHeight * 0.9
        },
        agentId,
        agentType,
        profile
      });

      // 设置初始不可见
      indoorSprite.visible = false;

      // 设置交互属性
      indoorSprite.interactive = true;
      indoorSprite.buttonMode = true;
      // 添加点击事件
      indoorSprite.on('click', (event) => {
        const cameraCtrl = gameStore.getCameraController;
        if (cameraCtrl && cameraCtrl.viewCharacterDetail) {
          cameraCtrl.viewCharacterDetail(indoorSprite.agentId, event);
        } else {
          console.warn('相机控制器未初始化，无法查看角色详情');
        }
      });
      
             indoorSprite.on('mouseover', (event) => {
         // 找到对应的角色数据并暂停移动
         const character = gameStore.characters.find(char => 
           (char.id === indoorSprite.agentId || char.agentId === indoorSprite.agentId)
         );
         
         if (character) {
           character.isPausedByHover = true;
           // 停止动画
           if (character.animatedSprite && character.animatedSprite.playing) {
             character.animatedSprite.stop();
             character.animatedSprite.gotoAndStop(0);
           }
         }
       });
       
       indoorSprite.on('mouseout', (event) => {
         // 找到对应的角色数据并恢复移动
         const character = gameStore.characters.find(char => 
           (char.id === indoorSprite.agentId || char.agentId === indoorSprite.agentId)
         );
         
         if (character) {
           character.isPausedByHover = false;
           // 如果角色正在移动状态，重启动画
           if (character.isMoving && character.animatedSprite && !character.animatedSprite.playing) {
             character.animatedSprite.play();
           }
         }
       });

      // 添加到目标精灵
      targetSprite.addChild(indoorSprite);

      return indoorSprite;
    };

    const generateAllIndoorCharacters = () => {
      // 检查是否有楼层精灵
      if (!isInitialized || !characterRenderer || !props.mapData || !sceneLayer) {
        console.error('未初始化，无法添加室内人物');
        return;
      }

      console.log('开始生成所有室内人物');

      // 检查是否还有可生成的人口容量
      const remainingCapacity = gameStore.remainingPopulation;
      if (remainingCapacity <= 0) {
        console.warn(`已达到最大人口容量${gameStore.populationCreated}，无法生成更多室内人物`);
        return;
      }

      // 已生成的室内人物总数
      let totalIndoorCharactersAdded = 0;

      // 收集所有可用于放置人物的楼层
      const availableFloors = [];

      // 首先收集所有可用的楼层
      for (let i = 0; i < sceneLayer.children.length; i++) {
        const sprite = sceneLayer.children[i];

        // 检查是否是建筑精灵，并且有buildingId属性
        if (sprite.buildingId) {
          // 如果是建筑容器，需要遍历其子元素找到楼层精灵
          if (sprite.children && sprite.children.length > 0) {
            for (let j = 0; j < sprite.children.length; j++) {
              const floorSprite = sprite.children[j];

              // 跳过屋顶精灵(通常是第一个子元素)
              if (j === 0) continue;

              // 检查是否有室内地板精灵
              if (floorSprite.room) {
                // 预先初始化室内人物数组到室内地板精灵
                if (!floorSprite.room.indoorCharacters) {
                  floorSprite.room.indoorCharacters = [];
                }

                // 获取建筑宽度用于计算容量
                const buildingWidth = sprite.buildingGridWidth || 2;

                // 使用unitCapacity计算每个楼层的人物容量
                const characterCapacity = buildingWidth * gameStore.unitCapacity;

                // 添加到可用楼层列表，包含容量信息
                availableFloors.push({
                  sprite: floorSprite,
                  room: floorSprite.room, // 存储室内地板引用
                  capacity: characterCapacity,
                  buildingId: sprite.buildingId,
                  floorIndex: j
                });
              } else {
                // 预先初始化室内人物数组
                if (!floorSprite.indoorCharacters) {
                  floorSprite.indoorCharacters = [];
                }

                // 获取建筑宽度用于计算容量
                const buildingWidth = sprite.buildingGridWidth || 2;

                // 使用unitCapacity计算每个楼层的人物容量
                const characterCapacity = buildingWidth * gameStore.unitCapacity;

                // 添加到可用楼层列表，包含容量信息
                availableFloors.push({
                  sprite: floorSprite,
                  capacity: characterCapacity,
                  buildingId: sprite.buildingId,
                  floorIndex: j
                });
              }
            }
          } else {
            // 如果是单层建筑，直接处理
            // 预先初始化室内人物数组
            if (!sprite.indoorCharacters) {
              sprite.indoorCharacters = [];
            }

            // 获取建筑宽度用于计算容量
            const buildingWidth = sprite.buildingGridWidth || 2;

            // 使用unitCapacity计算每个楼层的人物容量
            const characterCapacity = buildingWidth * gameStore.unitCapacity;

            // 添加到可用楼层列表
            availableFloors.push({
              sprite: sprite,
              capacity: characterCapacity,
              buildingId: sprite.buildingId,
              floorIndex: 0  // 单层建筑
            });
          }
        }
      }

      console.log(`总共找到${availableFloors.length}个可用楼层`);

      // 循环生成人物，每次每个建筑生成一个，直到达到人口上限或所有建筑都满了
      let hasAddedCharacter = true; // 标记是否有新人物被添加
      // 添加标志来检测是否已用尽代理
      let noMoreAgents = false;
      
      while (hasAddedCharacter && gameStore.remainingPopulation > 0 && availableFloors.length > 0 && !noMoreAgents) {
        hasAddedCharacter = false; // 重置标记
        
        // 遍历所有可用楼层
        for (let i = 0; i < availableFloors.length && gameStore.remainingPopulation > 0 && !noMoreAgents; i++) {
          const floor = availableFloors[i];
          const { sprite, room, capacity, buildingId, floorIndex } = floor;
          // 判断是使用room还是sprite来存储室内人物
          const targetSprite = room || sprite;
          
          // 检查当前楼层是否已满
          const currentCount = targetSprite.indoorCharacters ? targetSprite.indoorCharacters.length : 0;
          
          if (currentCount < capacity) {
            // 为当前楼层添加一个人物
            const indoorSprite = addCharacterIndoor(sprite);
            
            if (indoorSprite) {
              if (!targetSprite.indoorCharacters) {
                targetSprite.indoorCharacters = [];
              }
              
              // 如果有room，则将人物添加到room中
              if (room) {
                // 将人物从原来的父精灵移到room中
                sprite.removeChild(indoorSprite);
                room.addChild(indoorSprite);
              }
              
              targetSprite.indoorCharacters.push(indoorSprite);
              totalIndoorCharactersAdded++;
              hasAddedCharacter = true;
              
              // 如果当前楼层已满，可以从数组中移除
              if (targetSprite.indoorCharacters.length >= capacity) {
                availableFloors.splice(i, 1);
                i--; // 调整索引
              }
              
              // 如果已达到人口上限，退出循环
              if (gameStore.remainingPopulation <= 0) {
                break;
              }
            } else {
              // 如果返回null，可能是因为没有可用的agents
              // 检查addCharacterIndoor的实现，它在没有可用agents时返回null
              console.warn(`为建筑${buildingId}的楼层${floorIndex}添加室内人物失败`);
              
              // 检查agentGenerationQueue是否为空，如果为空则设置标志为true并跳出循环
              if (agentGenerationQueue.value.length === 0) {
                noMoreAgents = true;
                console.log('代理生成队列已用尽，停止生成室内人物');
                break;
              }
              
              // 如果添加失败但不是因为没有可用agents，从可用楼层中移除
              availableFloors.splice(i, 1);
              i--; // 调整索引
            }
          } else {
            // 当前楼层已满，从可用楼层中移除
            availableFloors.splice(i, 1);
            i--; // 调整索引
          }
        }
      }

      // 更新人口计数
      if (totalIndoorCharactersAdded > 0) {
        gameStore.addPopulationCreated(totalIndoorCharactersAdded);
        console.log(`总共生成了${totalIndoorCharactersAdded}个室内人物，平均分布在各个建筑中`);
      }
    }
    // 注册相机控制器方法（供MapCamera组件调用）
    const registerCameraController = (controller) => {
      console.log('注册相机控制器:', controller);
      cameraController = controller;
      
      // 将相机控制器保存到gameStore中全局共享
      gameStore.setCameraController(controller);
    };

    return {
      tilemapRootContainer,
      dispose,
      addCharacter,
      addCharacterOutSide,
      addCharacterIndoor,
      generateAllIndoorCharacters,
      isDevMode,
      getAgentMapping,
      registerCameraController
    };
  }
};
</script>

<style scoped>
.tilemap-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}
</style>