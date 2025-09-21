/**
 * 人物工厂类
 * 用于创建和管理场景中的人物角色
 */
import * as PIXI from 'pixi.js';
// 引入游戏状态管理store
import { useGameStore } from '../../stores/gameStore';
// 引入人物行为控制器
import CharacterBehavior from './CharacterBehavior';

class CharacterFactory {
  constructor() {
    this.characterTextures = {}; // 缓存生成的人物纹理
    this.headTextures = {}; // 缓存生成的头部纹理
    this.buildingCharacters = new Map(); // 存储进入建筑的人物 Map<buildingId, Array<character>>
    this.characterCounter = 0;   // 用于生成唯一人物ID的计数器
    this.initializeStyles();
    this.characterPositions = new Map(); // 存储所有人物当前位置，用于避免碰撞

    // 实例化行为控制器
    this.behaviorController = new CharacterBehavior();

    // 获取游戏状态store实例
    this.gameStore = null;

    // 在组件挂载后的下一个tick初始化游戏store
    this.initGameStore();
  }

  /**
   * 初始化gameStore
   */
  initGameStore() {
    this.gameStore = useGameStore();
  }

  /**
   * 获取游戏状态
   */
  isGamePaused() {
    return this.gameStore ? this.gameStore.isPaused : false;
  }

  /**
   * 获取游戏速度
   */
  getGameSpeed() {
    return this.gameStore ? this.gameStore.gameSpeed : 1;
  }

  /**
   * 初始化人物样式
   */
  initializeStyles() {
    // 定义不同人物类型的样式
    this.styles = {
      // 人物类型
      characterTypes: {
        "government": { // 政府官员
          id: "1", // 对应资源目录1_x
          colors: [
            0x1A5276, // 深蓝色
            0x154360, // 深蓝偏黑
            0x212F3C, // 深灰蓝
            0x283747  // 深蓝黑色
          ],
          speed: 1.5,
          size: 0.1,
          features: {
            hasTie: true,
            hasBriefcase: true,
            formalWear: true
          }
        },
        "researcher": { // 研究者/学者
          id: "2", // 对应资源目录2_x
          colors: [
            0x7D3C98, // 紫色
            0x5B2C6F, // 深紫色
            0x2471A3, // 蓝色
            0x17202A  // 黑色
          ],
          speed: 1.3,
          size: 0.1,
          features: {
            hasGlasses: true,
            hasBook: true
          }
        },
        "worker": { // 劳动者/工人
          id: "3", // 对应资源目录3_x
          colors: [
            0x7F8C8D, // 灰色
            0x2E86C1, // 工装蓝
            0x1E8449, // 工装绿
            0xA04000  // 棕色工装
          ],
          speed: 1.6,
          size: 0.1,
          features: {
            hasHelmet: true,
            workClothes: true
          }
        },
        "merchant": { // 商人
          id: "4", // 对应资源目录4_x
          colors: [
            0x2E4053, // 深蓝色西装
            0x7E5109, // 棕色
            0x1C2833, // 深色
            0x784212  // 棕红色
          ],
          speed: 1.7,
          size: 0.1,
          features: {
            hasTie: true,
            businessAttire: true
          }
        },
        "citizen": { // 公民
          id: "5", // 对应资源目录5_x
          colors: [
            0xE74C3C, // 红色
            0x3498DB, // 蓝色
            0x2ECC71, // 绿色
            0xF1C40F, // 黄色
            0x9B59B6  // 紫色
          ],
          speed: 1.4,
          size: 0.1,
          features: {
            casualWear: true
          }
        }
      }
    };
  }

  /**
   * 获取随机颜色
   * @param {Array} colorOptions 可选颜色数组
   * @returns {number} 随机选择的颜色
   */
  getRandomColor(colorOptions) {
    return colorOptions[Math.floor(Math.random() * colorOptions.length)];
  }

  /**
   * 获取随机人物类型
   * @returns {string} 随机人物类型
   */
  getRandomCharacterType() {
    const types = Object.keys(this.styles.characterTypes);
    return types[Math.floor(Math.random() * types.length)];
  }

  /**
   * 渲染人物纹理
   * @param {string} characterType 人物类型
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {PIXI.Application} app PIXI应用实例
   * @returns {PIXI.Container} 人物容器
   */
  renderCharacter(characterType, tileWidth, tileHeight, app) {
    const modelOptions = window.finalResult;
    // 获取人物风格
    const style = this.styles.characterTypes[characterType] || this.styles.characterTypes["citizen"];

    // 计算人物实际尺寸
    const size = Math.min(tileWidth, tileHeight) * style.size;

    // 随机选择性别 (50%几率选择男性或女性)
    const gender = Math.random() < 0.5 ? 'm' : 'f';

    // 使用角色类型对应的id
    // 使用传入的角色类型对应的ID而不是固定值
    const characterId = style.id || "5"; // 默认为5(公民)
    
    // 从finalResult中获取该类型角色的变种数量
    let variantCount = 1; // 默认只有1种变种
    
    // 检查window.finalResult是否存在并且包含character数据
    if (window.finalResult && 
        window.finalResult.character && 
        window.finalResult.character[gender] && 
        window.finalResult.character[gender][characterId]) {
      // 获取变种数量
      variantCount = window.finalResult.character[gender][characterId];
    }
    
    // 随机选择一个变种(1到variantCount之间的整数)
    const selectedVariant = Math.floor(Math.random() * variantCount) + 1;

    // 组合成资源路径格式：character/gender/a_b
    const characterPath = `${gender}/${characterId}_${selectedVariant}`;

    // 生成一个唯一的头部配置
    const headConfig = this.generateRandomHeadConfig(gender);


    // 创建人物容器
    const container = new PIXI.Container();

    // 使用配置获取头部纹理
    const headTexture = this.generateHeadTexture(gender, headConfig, app);

    // 使用动画帧创建动画精灵 - 需要调整路径以使用新结构
    // 检查是否有对应的动画序列
    const walkAnimationKey = `character/${characterPath}`;
    const walkFrames = window.animations[walkAnimationKey];

    // 创建身体动画精灵
    let body;

    if (walkFrames && walkFrames.length > 0) {
      // 检查walkFrames的第一个元素是否已经是Texture对象
      if (walkFrames[0] instanceof PIXI.Texture) {
        // 直接使用walkFrames作为纹理数组
        body = new PIXI.AnimatedSprite(walkFrames);
      } else {
        // 如果是字符串路径，则转换为纹理对象
        const walkTextures = walkFrames.map(path => window.textures[path]);
        body = new PIXI.AnimatedSprite(walkTextures);
      }
      // 设置动画属性
      body.animationSpeed = 0.15;
      body.loop = true;
      // 默认先停止动画，只有移动时才播放
      body.stop();

      // 设置精灵尺寸和位置
      body.position.set(0, 0);
      // 调整精灵尺寸为固定值，而不是修改纹理
      body.width = body.width / 7;
      body.height = body.height / 7;
    } else {
      // 如果没有可用的动画帧，创建一个普通精灵作为后备
      // 使用第一个基本动作帧
      const bodyTexturePath = `character/${characterPath}/1.png`;
      const bodyTexture = window.textures[bodyTexturePath];

      // 如果没有找到特定类型的纹理，使用备用纹理
      const fallbackTexturePath = `character/f/1_1/1.png`;
      body = new PIXI.Sprite(bodyTexture || window.textures[fallbackTexturePath]);
      body.position.set(0, 0);
      // 调整精灵尺寸为固定值，而不是修改纹理
      body.width = body.width / 7;
      body.height = body.height / 7;
    }

    // 添加身体到容器
    container.addChild(body);

    // 添加头部到容器
    if (headTexture) {
      // 创建头部精灵
      const headSprite = new PIXI.Sprite(headTexture);
      headSprite.width = headSprite.width / 7;
      headSprite.height = headSprite.height / 7;
      headSprite.position.set(body.width / 2 - headSprite.width / 2, -headSprite.height); // 居中并置于身体上方

      // 添加到人物容器
      container.addChild(headSprite);

      // 保存头部配置
      container.headConfig = headConfig;
    }

    // 设置整体尺寸
    container.width = size;
    container.height = size;

    // 保存角色的性别和类型信息
    container.gender = gender;
    container.characterId = characterId;
    container.variantId = selectedVariant;


    return container;
  }

  /**
   * 生成随机头部配置
   * @param {string} gender 性别(m/f)
   * @returns {Object} 头部配置
   */
  generateRandomHeadConfig(gender) {
    const modelOptions = window.finalResult;
    // 如果没有头部资源，返回空配置
    if (!modelOptions || !modelOptions.head || !modelOptions.head[gender]) {
      return {};
    }

    // 头部部件类型
    const partTypes = ['f', 'e', 'm', 'h']; // 脸型、眼睛、嘴巴、头发

    // 创建配置对象
    const config = {};

    // 使用当前时间和一个随机数作为种子，确保每次调用都产生不同的结果
    const seed = Date.now() + Math.random() * 10000;

    // 为每种部件类型随机选择一个部件
    partTypes.forEach((partType, index) => {
      if (modelOptions.head[gender][partType]) {
        const partCount = modelOptions.head[gender][partType];

        if (partCount > 0) {
          // 使用index作为附加随机因子，确保每种部件使用不同的随机值
          const randomSeed = seed + index * 137; // 质数137作为乘数避免模式
          // 随机选择一个部件编号(1到partCount之间)
          const randomValue = Math.floor(Math.random() * randomSeed) % partCount + 1;
          config[partType] = randomValue > partCount ? partCount : randomValue;
        }
      }
    });

    return config;
  }

  /**
   * 从head资源中生成头部纹理
   * @param {string} gender 性别(m/f)
   * @param {Object} config 部件配置，如 {f: 1, e: 2, m: 1, h: 3}
   * @param {PIXI.Application} app PIXI应用实例，用于创建RenderTexture
   * @returns {PIXI.Texture} 头部纹理
   */
  generateHeadTexture(gender, config, app) {
    // 创建缓存键
    const cacheKey = `head_${gender}_f${config.f || 0}_e${config.e || 0}_m${config.m || 0}_h${config.h || 0}`;

    // 检查缓存中是否已有该头部纹理
    if (this.headTextures[cacheKey]) {
      return this.headTextures[cacheKey];
    }

    // 检查是否有head资源
    const modelOptions = window.finalResult;
    if (!modelOptions || !modelOptions.head || !modelOptions.head[gender]) {
      console.warn('没有可用的头部资源');
      return null;
    }

    // 创建临时容器用于渲染
    const tempContainer = new PIXI.Container();
    // 启用排序功能
    tempContainer.sortableChildren = true;

    // 记录容器尺寸
    let containerWidth = 0;
    let containerHeight = 0;

    // 用于跟踪头发部件的引用和尺寸
    let hairSprite = null;
    let hairHeight = 0;
    let hairWidth = 0;

    // 检查头发是否有下半部分
    let hasHairLowerPart = false;
    if (config.h) {
      const hairLowerPartPath = `head/${gender}/h/${config.h}_0.png`;
      hasHairLowerPart = window.textures[hairLowerPartPath] != null;
    }

    // 定义部件的zIndex值
    const zIndexMap = {
      'f': 4,  // 脸型
      'e': 5,  // 眼睛
      'm': 5,  // 嘴巴
      'h': 6   // 头发(顶层)
    };

    // 按顺序添加部件
    ['f', 'e', 'm', 'h'].forEach(partType => {
      // 检查配置中是否有该部件
      if (config[partType]) {
        // 生成部件的纹理路径
        const partTexturePath = `head/${gender}/${partType}/${config[partType]}.png`;

        // 获取纹理对象
        const partTexture = window.textures[partTexturePath];

        if (partTexture) {
          // 创建部件精灵
          const partSprite = new PIXI.Sprite(partTexture);

          // 居中部件
          partSprite.anchor.set(0.5, 0.5);

          // 设置zIndex
          partSprite.zIndex = zIndexMap[partType];

          // 更新容器尺寸
          containerWidth = Math.max(containerWidth, partTexture.width);
          containerHeight = Math.max(containerHeight, partTexture.height);

          // 如果是头发部件，保存引用和尺寸
          if (partType === 'h') {
            hairSprite = partSprite;
            hairWidth = partTexture.width;
            hairHeight = partTexture.height;
          }

          // 将精灵添加到容器
          tempContainer.addChild(partSprite);
        } else {
          console.warn(`找不到部件纹理: ${partTexturePath}`);
        }
      }
    });

    // 调整所有部件位置
    tempContainer.children.forEach(child => {
      // 头发部件放在顶部
      if (child === hairSprite) {
        // 头发部件放在顶部中心
        child.position.set(containerWidth / 2, hairHeight / 2);
      } else {
        // 其他部件居中放置
        child.position.set(containerWidth / 2, containerHeight / 2);
      }
    });

    // 添加头发下半部分（如果存在）
    if (hasHairLowerPart && config.h && hairSprite) {
      const hairLowerPartPath = `head/${gender}/h/${config.h}_0.png`;
      const hairLowerPartTexture = window.textures[hairLowerPartPath];

      if (hairLowerPartTexture) {
        // 创建头发下半部分精灵
        const hairLowerSprite = new PIXI.Sprite(hairLowerPartTexture);

        // 设置锚点以便于定位
        hairLowerSprite.anchor.set(0.5, 0);

        // 设置zIndex
        hairLowerSprite.zIndex = 3; // 头发下半部分的zIndex为3

        // 定位在头发下方紧贴着
        hairLowerSprite.position.set(
          containerWidth / 2, // x坐标居中
          hairSprite.position.y + hairHeight / 2 // y坐标紧贴头发底部
        );

        // 将精灵添加到容器
        tempContainer.addChild(hairLowerSprite);
      }
    }

    // 排序子元素，确保zIndex生效
    tempContainer.sortChildren();

    // 使用应用渲染器创建纹理
    let texture;
    if (app && app.renderer) {
      // 创建渲染纹理
      texture = PIXI.RenderTexture.create({
        width: containerWidth,
        height: containerHeight
      });

      // 将容器渲染到纹理
      app.renderer.render(tempContainer, { renderTexture: texture });
    } else {
      console.warn('无法创建渲染纹理，应用或渲染器未初始化');
      return null;
    }

    // 清理临时容器
    tempContainer.destroy({ children: true });

    // 将生成的纹理存入缓存
    this.headTextures[cacheKey] = texture;

    return texture;
  }

  /**
   * 为人物创建阴影
   * @param {PIXI.Container} sprite 人物容器
   * @param {boolean} isIndoor 是否为室内人物
   * @returns {PIXI.Sprite} 阴影精灵
   */
  createCharacterShadow(sprite, isIndoor = false) {
    // 创建一个简单的椭圆形阴影，而不是使用精灵的纹理
    const shadow = new PIXI.Graphics();

    // 设置阴影的填充颜色和透明度
    shadow.beginFill(0x000000, 0.4);

    // 绘制椭圆形阴影，宽度为精灵宽度的60%，高度为宽度的40%
    const shadowWidth = sprite.width * 0.6;
    const shadowHeight = shadowWidth * 0.4;
    shadow.drawEllipse(0, 0, shadowWidth / 2, shadowHeight / 2);
    shadow.endFill();

    // 设置阴影位置在人物脚下中央
    // 由于精灵的pivot设置在底部中心，我们需要将阴影放在相同位置
    shadow.x = sprite.width / 2;
    shadow.y = sprite.height * 0.7;

    // 设置zIndex确保阴影始终在人物下方
    shadow.zIndex = -1;

    // 如果是室内人物，设置阴影为不可见
    shadow.visible = !isIndoor;

    // 将阴影添加为人物的子元素，这样它会随人物移动
    sprite.addChild(shadow);

    return shadow;
  }

  /**
   * 创建人物精灵（统一方法）
   * @param {Object} options 创建选项
   * @returns {PIXI.Sprite} 人物精灵
   */
  createCharacter(options) {
    // 解构参数
    const {
      x, y, gridX, gridY, tileWidth, tileHeight, app,
      isIndoor = false, parentSprite = null, bounds = null,
      agentId = null, agentType = null, profile = {} // 新增agentId和agentType参数
    } = options;

    // 生成唯一人物ID
    const prefix = isIndoor ? 'indoor_character_' : 'character_';
    const characterId = `${prefix}${++this.characterCounter}`;

    // 使用传入的agentType或随机选择人物类型
    const characterType = agentType || this.getRandomCharacterType();
    const style = this.styles.characterTypes[characterType];

    // 创建角色精灵容器
    const sprite = new PIXI.Container();

    // 获取人物容器 (包含动画精灵)
    const characterContainer = this.renderCharacter(characterType, tileWidth, tileHeight, app);
    const gender = characterContainer.gender;

    // 由于Container没有clone方法，需要手动复制内容
    let animatedSprite = null;

    // 遍历容器的所有子元素并添加到角色精灵中
    if (characterContainer && characterContainer.children) {
      for (let i = 0; i < characterContainer.children.length; i++) {
        const child = characterContainer.children[i];

        // 复制子精灵
        let childCopy;

        if (child instanceof PIXI.AnimatedSprite) {
          // 如果是AnimatedSprite，需要创建新的实例
          childCopy = new PIXI.AnimatedSprite(child.textures);
          childCopy.animationSpeed = child.animationSpeed;
          childCopy.loop = child.loop;
          childCopy.gotoAndStop(0); // 设置到第一帧

          // 保存动画精灵引用
          animatedSprite = childCopy;
        } else if (child instanceof PIXI.Sprite) {
          // 如果是普通精灵，复制它
          childCopy = new PIXI.Sprite(child.texture);
          childCopy.tint = child.tint;
          childCopy.alpha = child.alpha;
        } else {
          // 其他类型元素，跳过
          continue;
        }

        // 复制位置和尺寸属性
        childCopy.position.set(child.position.x, child.position.y);
        if (child.width) childCopy.width = child.width;
        if (child.height) childCopy.height = child.height;

        // 复制滤镜
        if (child.filters && child.filters.length > 0) {
          childCopy.filters = [...child.filters];
        }

        // 添加到角色容器
        sprite.addChild(childCopy);
      }
    }

    // 调整锚点，使精灵的底部中心作为原点
    sprite.pivot.x = sprite.width / 2;
    sprite.pivot.y = sprite.height;

    // 设置初始位置
    sprite.x = x;
    sprite.y = y;
    // 设置初始zIndex
    sprite.zIndex = y;
    // 设置初始朝向（水平翻转）
    sprite.scale.x = -1;
    sprite.eventMode = 'static'; // 允许交互
    sprite.cursor = 'pointer';   // 鼠标悬停时显示小手

    // 如果是室内人物，初始设置为不可见
    if (isIndoor) {
      sprite.visible = false;
    }

    // 为人物创建阴影，传入isIndoor参数
    const shadow = this.createCharacterShadow(sprite, isIndoor);
    sprite.shadow = shadow;
    // 创建人物数据对象 - 合并室内外人物字段
    const characterData = {
      id: characterId,
      type: characterType,
      sprite: sprite,
      shadow: shadow, // 存储阴影引用
      animatedSprite: animatedSprite, // 存储动画精灵引用
      avatarConfig: characterContainer.headConfig, // 存储头像路径
      gender: gender, // 存储性别
      isIndoor: isIndoor,  // 标记是否为室内人物
      isWorking: 0,
      isMoving: false,   // 标记是否正在工作
      isFocused: false, // 标记是否被聚焦 
      isVisible: false, // 标记是否在视口中可见
      x: x,
      y: y,
      targetX: x,
      targetY: y,
      speed: isIndoor ? style.speed * 0.5 : style.speed, // 室内人物速度减半
      moveTimer: 0,
      moveInterval: isIndoor ? 3000 : 2000 + Math.random() * 2000, // 移动间隔
      lastUpdateTime: Date.now(),
      agentId: agentId, // 绑定agentId
      agentType: characterType, // 存储agentType
      profile: profile, // 存储profile
      bounds: bounds || null, // 移动边界
      buildingId: parentSprite ? parentSprite.uid : null,
      parentSprite: parentSprite || null,
    };

    // 室外人物特有属性
    if (!isIndoor) {
      Object.assign(characterData, {
        gridX: gridX,
        gridY: gridY,
        targetGridX: gridX,
        targetGridY: gridY,
        isGoingToBuilding: false,     // 是否正在前往建筑
        targetBuilding: null,         // 目标建筑
        buildingStayTime: 0,          // 在建筑内停留时间
        buildingId: null,             // 所在建筑物ID
        buildingInterval: 20000 + Math.random() * 40000, // 进入建筑间隔，毫秒
        lastBuildingTime: Date.now() - (10000 + Math.random() * 10000) // 初始随机化，避免所有人同时进入建筑
      });
    }

    // 将人物ID和类型附加到精灵上
    sprite.characterId = characterId;
    sprite.characterType = characterType;
    sprite.isIndoor = isIndoor;
    sprite.agentId = agentId; // 将agentId添加到精灵上

    // 将人物数据存储到gameStore中
    if (this.gameStore) {
      // console.log('characterData:', characterData);
      this.gameStore.addCharacter(characterData);
    } else {
      console.warn('gameStore未初始化，无法添加人物数据');
    }

    return sprite;
  }

  /**
   * 创建室外人物精灵（向下兼容的方法）
   * @param {Object} options 创建选项
   * @returns {PIXI.Sprite} 人物精灵
   */
  createOutdoorCharacter(options) {
    // 设置isIndoor为false，使用统一的创建方法
    return this.createCharacter({ ...options, isIndoor: false });
  }

  /**
   * 创建室内人物精灵（向下兼容的方法）
   * @param {Object} options 创建选项 
   * @returns {PIXI.Sprite} 人物精灵
   */
  createIndoorCharacter(options) {
    // 设置isIndoor为true，使用统一的创建方法
    return this.createCharacter({ ...options, isIndoor: true });
  }

  /**
   * 为角色添加对话气泡
   * @param {Object} character 角色对象
   */
  addBubbleToCharacter(character) {
    if (!character.sprite || character.bubbleSprite) return;
    const workingtype = character.isWorking; // 获取工作类型数字

    // 根据不同的工作类型选择不同的气泡纹理
    let bubbleTexturePath = "bubble/1.png"; // 默认气泡

    // 根据工作类型选择不同的气泡
    switch (workingtype) {
      case 1: // 近距离交流
        bubbleTexturePath = "bubble/1.png";
        break;
      case 2: // 远距离交流
        bubbleTexturePath = "bubble/2.png";
        break;
      case 3: // 其他类型
        bubbleTexturePath = "bubble/3.png";
        break;
      case 4: // 开始事件
        bubbleTexturePath = "bubble/4.png";
        break;
      default: // 默认或未知类型
        bubbleTexturePath = "bubble/1.png";
    }

    // 使用选择的气泡纹理创建精灵
    const bubbleTexture = window.textures[bubbleTexturePath];
    if (!bubbleTexture) {
      console.warn(`气泡纹理未找到: ${bubbleTexturePath}`);
      return;
    }

    const bubble = new PIXI.Sprite(bubbleTexture);

    // 确保气泡位置相对于角色是固定的
    bubble.anchor.set(0, 1); // 设置锚点在底部中心

    // 设置气泡位置在角色头部右上方
    bubble.x = character.sprite.width / 5; // 右侧偏移，减去一点以避免太偏
    bubble.y = -character.sprite.height / 5; // 头部上方

    // 存储气泡引用
    character.bubbleSprite = bubble;

    // 设置气泡的zIndex确保它总是在角色上方
    bubble.zIndex = character.sprite.zIndex;
    character.sprite.addChild(bubble);


    // 强制更新渲染，确保气泡位置正确
    if (character.sprite.parent) {
      character.sprite.parent.sortChildren();
    }
  }

  /**
   * 从角色移除对话气泡
   * @param {Object} character 角色对象
   */
  removeBubbleFromCharacter(character) {
    if (!character.sprite || !character.bubbleSprite) return;

    // 从角色精灵中移除气泡
    character.sprite.removeChild(character.bubbleSprite);

    // 销毁气泡精灵
    character.bubbleSprite.destroy();

    // 移除气泡引用
    character.bubbleSprite = null;
  }

  /**
   * 更新人物移动
   * @param {number} deltaTime 时间差
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @param {Object} navigationGraph 导航图
   */
  updateCharacters(deltaTime, tileWidth, tileHeight, mapWidth, mapHeight) {
    // 如果游戏暂停，则不更新人物
    if (this.isGamePaused()) {
      return;
    }

    // 确保行为控制器已初始化
    if (!this.behaviorController) {
      return;
    }

    // 获取gameStore
    const gameStore = this.gameStore;
    // 应用游戏速度
    const speedMultiplier = this.getGameSpeed();
    const adjustedDeltaTime = deltaTime * speedMultiplier;

    const currentTime = Date.now();

    // 清除之前的位置映射
    this.characterPositions.clear();

    // 获取当前视口信息
    const viewport = gameStore.getViewport;

    // 如果视口不存在，不进行处理
    if (!viewport) {
      return;
    }

    // 计算视口范围（比实际视口稍大，以便优化边界角色的进出）
    const viewportBounds = {
      left: viewport.left - tileWidth * 2,
      right: viewport.right + tileWidth * 2,
      top: viewport.top - tileHeight * 2,
      bottom: viewport.bottom + tileHeight * 2
    };

    // 检查角色是否在视口内的函数
    const isInViewport = (character) => {
      // 室内人物由所在建筑物决定可见性
      if (character.isIndoor) {
        return character.sprite && character.sprite.visible;
      }

      // 室外人物根据位置判断是否在视口内
      return character.x >= viewportBounds.left &&
        character.x <= viewportBounds.right &&
        character.y >= viewportBounds.top &&
        character.y <= viewportBounds.bottom;
    };

    // 预先筛选需要更新的角色
    const visibleCharacters = gameStore.characters.filter(char => {
      // 必须有sprite并且sprite必须存在
      if (!char.sprite) return false;

      // 检查角色之前是否可见
      const wasVisible = char.isVisible;

      // 计算当前是否可见
      const isVisible = isInViewport(char);

      // 更新可见状态
      char.isVisible = isVisible;

      // 如果可见状态发生变化，需要更新
      const visibilityChanged = wasVisible !== isVisible;

      // 室内人物需要特殊处理：只有在建筑物被hover显示时才更新
      if (char.isIndoor) {
        // 如果不可见，不需要更新
        if (!isVisible) return false;

        // 如果父精灵存在且可见，说明建筑被hover显示，需要更新
        return char.sprite.visible === true;
      }

      // 如果是焦点角色，无论是否可见都需要更新
      if (char.isFocused) return true;

      // 如果可见或者可见性刚刚变化，需要更新
      return isVisible || visibilityChanged;
    });

    // 记录所有可见室外人物当前位置
    visibleCharacters.forEach(character => {
      if (!character.isIndoor) {
        // 只记录室外人物
        const positionKey = `${Math.floor(character.x / tileWidth)},${Math.floor(character.y / tileHeight)}`;
        this.characterPositions.set(positionKey, character);

        // 实时更新zIndex，即使没有移动也更新
        if (character.sprite) {
          // character.sprite.zIndex = character.y;
        }
      }
    });

    // 将角色位置信息传递给行为控制器
    this.behaviorController.setCharacterPositions(this.characterPositions);

    // 将视口信息传递给行为控制器
    this.behaviorController.setViewportBounds(viewportBounds, tileWidth, tileHeight);

    // 遍历所有需要更新的人物
    for (const character of visibleCharacters) {
      character.moveTimer += adjustedDeltaTime * 1000;  // 转换为毫秒

      // 实时更新人物的zIndex，确保正确的层级关系
      if (character.sprite) {
        character.sprite.zIndex = character.y;

        // 为工作中的人物添加颜色标识
        if (character.isWorking !== 0) {  // 修改：任何非0的isWorking视为true
          // 添加气泡图标
          if (!character.bubbleSprite) {
            this.addBubbleToCharacter(character);
          }

          // 如果是室外人物且处于工作状态，那么重置前往建筑的标志
          if (!character.isIndoor) {
            // 如果角色当前正在前往建筑，重置此状态
            if (character.isGoingToBuilding) {
              character.isGoingToBuilding = false;
              character.targetBuilding = null;
              character.isSearchingBuilding = false;
              // console.log(`角色${character.id}由于开始工作，取消前往建筑`);

              // 重置路径点，使其回到路上移动
              character.pathPoints = [];
            }
          }
        } else {
          // 移除气泡图标
          if (character.bubbleSprite) {
            this.removeBubbleFromCharacter(character);
          }
        }
      }

      // 根据不同状态，调用行为控制器的不同方法更新角色
      if (character.isWorking !== 0) {
        // 工作状态
        this.behaviorController.updateWorkingCharacter(character, adjustedDeltaTime, tileWidth, tileHeight);

        // 修改: 工作中的角色到达目的地后，不再随机移动，而是保持静止直到工作状态结束
        // 如果工作中的角色停止移动，不再让他随机移动
        if (!character.isMoving) {
          // 重置移动计时器，避免累积
          character.moveTimer = 0;
          character.lastUpdateTime = currentTime;

          // 确保角色停在原地，而不是随机移动
          // console.log(`角色${character.id}停止移动，不再让他随机移动`);
          if (character.animatedSprite && character.animatedSprite.playing) {
            character.animatedSprite.stop();
            character.animatedSprite.gotoAndStop(0); // 回到第一帧
          }
        }
      } else if (character.isMoving) {
        // 移动状态
        this.behaviorController.updateMovingCharacter(character, adjustedDeltaTime, tileWidth, tileHeight);
      } else if (character.moveTimer > character.moveInterval) {
        // 待机状态，时间到达移动间隔
        character.moveTimer = 0;
        character.lastUpdateTime = currentTime;

        if (character.isIndoor) {
          // 室内人物随机移动 - 只有在显示状态下才执行
          if (character.sprite && character.sprite.visible) {
            this.behaviorController.updateIndoorRandomMovement(character, adjustedDeltaTime, speedMultiplier);
          }
        } else {
          // 室外人物随机移动
          this.behaviorController.moveRandomly(character, tileWidth, tileHeight, mapWidth, mapHeight);
        }
      } else if (!character.isMoving && character.animatedSprite && character.animatedSprite.playing) {
        // 确保非移动状态下停止动画
        character.animatedSprite.stop();
        character.animatedSprite.gotoAndStop(0); // 回到第一帧
      }
    }
  }


  /**
   * 根据ID获取建筑数据
   * @param {string} buildingId 建筑ID
   * @returns {Object|null} 建筑数据
   */
  getBuildingById(buildingId) {
    const gameStore = this.gameStore || useGameStore();
    return gameStore.buildings && gameStore.buildings.find(b => b.id === buildingId) || null;
  }

  /**
   * 清理人物数据，但保留纹理缓存
   * 用于地图更新时重置人物，而不销毁纹理资源
   */
  clearCharacters() {
    // 清理人物数据数组
    if (this.gameStore) {
      this.gameStore.clearCharacters();
    }
    this.buildingCharacters.clear(); // 清理建筑内人物
    // 重置计数器，不重置计数器会导致ID持续增长
    this.characterCounter = 0;
  }

  /**
   * 清理资源
   */
  dispose() {
    // 清理纹理
    for (const key in this.characterTextures) {
      // 检查是否是Container，如果是，需要递归销毁子元素
      if (this.characterTextures[key] instanceof PIXI.Container) {
        this.characterTextures[key].destroy({ children: true });
      } else if (this.characterTextures[key].texture) {
        this.characterTextures[key].texture.destroy(true);
      }
    }
    this.characterTextures = {};

    // 清理头部纹理
    for (const key in this.headTextures) {
      if (this.headTextures[key]) {
        this.headTextures[key].destroy(true);
      }
    }
    this.headTextures = {};

    // 清理人物数据
    if (this.gameStore) {
      this.gameStore.clearCharacters();
    }
    this.buildingCharacters.clear(); // 清理建筑内人物
    this.characterCounter = 0;
  }
}

export default CharacterFactory; 