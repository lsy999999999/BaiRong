/**
 * 建筑绘制组件
 * 用于使用PIXI.Graphics绘制现代城市风格建筑 - 正面视角
 */
import * as PIXI from 'pixi.js';
import { useGameStore } from '../../stores/gameStore';

class BuildingRenderer {
  constructor() {
    this.buildingData = {};    // 存储建筑的额外数据（ID、层数等）
    this.buildingCounter = 0;  // 用于生成唯一建筑ID的计数器
    this.gameStore = null;     // 存储gameStore引用
    
    // 尝试初始化gameStore
    this.initGameStore();
  }
  
  /**
   * 初始化gameStore引用
   */
  initGameStore() {
    try {
      this.gameStore = useGameStore();
      console.log('BuildingRenderer: gameStore初始化成功');
    } catch (error) {
      console.warn('BuildingRenderer: gameStore初始化失败，将在需要时重试', error);
    }
  }
  
  /**
   * 确保gameStore可用
   */
  ensureGameStore() {
    if (!this.gameStore) {
      this.initGameStore();
    }
    return this.gameStore;
  }

  /**
   * 创建建筑并返回建筑精灵
   * @param {Object} buildingInfo 建筑信息对象
   * @param {number} buildingInfo.x 建筑在网格中的X坐标
   * @param {number} buildingInfo.y 建筑在网格中的Y坐标
   * @param {string} buildingInfo.type 建筑类型ID
   * @param {string} buildingInfo.style 建筑风格(house/villa等)
   * @param {number} buildingInfo.width 建筑宽度(格子数)
   * @param {number} buildingInfo.height 建筑高度(格子数)
   * @param {number} buildingInfo.floors 建筑楼层数
   * @param {number} tileWidth 瓦片宽度(像素)
   * @param {number} tileHeight 瓦片高度(像素)
   * @param {function} addIndoorCharacter 添加室内人物的函数
   * @returns {Object} 包含建筑精灵、建筑ID和建筑阴影的对象
   */
  createBuilding(buildingInfo, tileWidth, tileHeight, addIndoorCharacter = null) {
    // console.log('createBuilding', buildingInfo);
    const { x, y, type, width, height, floors } = buildingInfo;
    let sprite = null;
    let totalHeight = 0;

    // 创建建筑容器
    // 根据建筑类型获取可用的风格数量，默认为3种风格
    const modelOptions = window.finalResult[buildingInfo.style] &&
      window.finalResult[buildingInfo.style][type] ?
      window.finalResult[buildingInfo.style][buildingInfo.type] : 3;

    // 随机选择一种风格 (1到styleOptions之间的整数)
    const model = Math.floor(Math.random() * modelOptions) + 1;
    const buildingSprite = new PIXI.Container();

    if (buildingInfo.style === "house") {
      const base = new PIXI.Sprite(window.textures[`house/${type}/${type}_${model}_0.png`]);
      base.width = width * tileWidth;
      base.height = base.height;

      const floor = new PIXI.Sprite(window.textures[`house/${type}/${type}_${model}_1.png`]);
      floor.width = width * tileWidth;
      floor.height = floor.height;

      const roof = new PIXI.Sprite(window.textures[`house/${type}/${type}_${model}_2.png`]);
      roof.width = width * tileWidth;
      roof.height = roof.height;

      // 添加建筑部件
      let currentY = 0;
      // 计算楼层数量
      const floorCount = floors <= 1 ? 1 : floors - 1;
      // 正确计算总高度：屋顶 + n个楼层 + 底座
      totalHeight = base.height + (floorCount * floor.height) + roof.height;

      // 添加屋顶
      roof.y = currentY;
      currentY += roof.height * (1 - roof.anchor.y);
      buildingSprite.addChild(roof);

      // 循环添加多个楼层
      for (let i = 0; i < floorCount; i++) {
        const floorClone = new PIXI.Sprite(window.textures[`house/${type}/${type}_${model}_1.png`]);
        floorClone.width = width * tileWidth;
        floorClone.height = floorClone.height;
        floorClone.y = currentY;
        currentY += floor.height * (1 - floor.anchor.y);
        buildingSprite.addChild(floorClone);
      }

      // 添加底座
      base.y = currentY;
      currentY += base.height * (1 - base.anchor.y);
      buildingSprite.addChild(base);

      // 如果提供了添加室内人物的函数，则为所有子精灵添加交互事件
      if (addIndoorCharacter) {
        buildingSprite.children.forEach(sprite => {
          // 如果是屋顶(roof)，不添加交互事件和室内人物
          if (sprite === roof) {
            return; // 跳过屋顶
          }

          sprite.interactive = true;
          sprite.buttonMode = true;

          // 添加室内地板
          let roomTexture;
          if (sprite === base) {
            // 尝试使用4号图片，如果不存在则使用3号图片
            const texture4 = window.textures[`house/${type}/${type}_${model}_4.png`];
            roomTexture = texture4 ? texture4 : window.textures[`house/${type}/${type}_1_3.png`];
          } else {
            // 尝试使用3号图片，如果不存在则使用默认4号图片
            const texture3 = window.textures[`house/${type}/${type}_${model}_3.png`];
            roomTexture = texture3 ? texture3 : window.textures[`house/${type}/${type}_1_4.png`];
          }
          // console.log('roomTexture:', type,model);
          
          const room = new PIXI.Sprite(roomTexture);
          room.width = sprite.width;
          // 根据纹理的宽高比例计算高度，保持纹理原始比例
          const aspectRatio = roomTexture.height / roomTexture.width;
          room.height = room.width * aspectRatio;
          room.x = 0;
          // 从底部向上延申，将room底部对齐精灵底部
          room.y = sprite.height - room.height;
          room.visible = false; // 默认不可见
          sprite.addChild(room);
          sprite.room = room;

          // 添加存储室内人物的数组到室内地板
          room.indoorCharacters = [];
          sprite.hasAddedCharacters = false;

          // 创建并添加家具到室内地板
          const buildingWidth = width;
          // 为家具随机选择模型样式（1或2）
          const furnitureModel = Math.random() < 0.5 ? 1 : 2;
          const furnitureTexture = window.textures[`furniture/${buildingWidth}_${furnitureModel}.png`];
          
          if (furnitureTexture) {
            const furniture = new PIXI.Sprite(furnitureTexture);
            // 设置家具位置在室内地板中央
            furniture.x = room.width / 2 - furniture.width / 2;
            furniture.y = room.height / 2 - furniture.height;
            // 设置家具的zIndex较低，确保不会遮挡人物
            furniture.zIndex = 5;
            // 将家具添加到室内地板精灵中
            room.addChild(furniture);
            // 记录家具
            room.furniture = furniture;
          }

          sprite.onmouseenter = (event) => {
            // 不再改变透明度，而是直接显示室内地板
            
            // 保存原始zIndex
            sprite.originalZIndex = sprite.zIndex;
            // 提高zIndex使其高于其他楼层
            sprite.zIndex = 9999;
            
            // 设置标志表示当前正在被hover
            sprite.isBeingHovered = true;
            
            // 调整父容器中所有兄弟元素的zIndex
            if (sprite.parent && sprite.parent.children) {
              sprite.parent.children.forEach(sibling => {
                if (sibling !== sprite) {
                  // 保存兄弟元素的原始zIndex
                  sibling.originalZIndex = sibling.zIndex;
                  // 降低兄弟元素的zIndex
                  sibling.zIndex = 1000;
                }
              });
            }
            
            // 显示室内地板
            if (sprite.room) {
              sprite.room.visible = true;
              // 确保室内地板的zIndex高于当前sprite
              sprite.room.zIndex = 10000;
              
              // 如果有家具，确保家具的zIndex较低
              if (sprite.room.furniture) {
                sprite.room.furniture.zIndex = 10;
              }
              
            }
            
            // 确保有indoorCharacters数组
            if (sprite.room && sprite.room.indoorCharacters) {
              // 显示当前楼层的所有人物，并确保人物zIndex高于家具
              sprite.room.indoorCharacters.forEach(character => {
                character.visible = true;
                // 确保人物zIndex高于室内地板和家具
                character.zIndex = 10001;
              });
              
              // 显示所有子元素并设置正确的zIndex
              sprite.room.children.forEach(child => {
                // 如果是家具，设置较低的zIndex
                if (child === sprite.room.furniture) {
                  child.zIndex = 10;
                } 
                // 如果是人物，确保较高的zIndex
                else if (sprite.room.indoorCharacters.includes(child)) {
                  child.zIndex = 10001;
                }
                // 其他元素可见性设置
                child.visible = true;
              });
            }
          }

          sprite.onmouseleave = (event) => {
            // 检查鼠标是否在室内地板上，如果不在则隐藏
            if (sprite.room && !sprite.room.containsPoint(event.data.global)) {
              sprite.room.visible = false;
              
              // 隐藏当前楼层的所有人物
              if (sprite.room.indoorCharacters) {
                sprite.room.indoorCharacters.forEach(character => {
                  character.visible = false;
                });
              }
              
              // 恢复当前sprite的原始zIndex
              sprite.zIndex = sprite.originalZIndex;
              
              // 恢复所有兄弟元素的zIndex
              if (sprite.parent && sprite.parent.children) {
                sprite.parent.children.forEach(sibling => {
                  if (sibling !== sprite && sibling.originalZIndex !== undefined) {
                    sibling.zIndex = sibling.originalZIndex;
                  }
                });
              }
              
              // 移除hover标志
              sprite.isBeingHovered = false;
            }
          }
        });
      }

      // 减少宽度并水平居中
      buildingSprite.width = 0.9 * (width * tileWidth);
      buildingSprite.height = 0.9 * totalHeight;
      buildingSprite.zIndex = (y + height) * tileHeight;
    } else if (buildingInfo.style === "villa") {
      const villa = new PIXI.Sprite(window.textures[`villa/${type}/${type}_${model}.png`]);
      villa.width = width * tileWidth;
      villa.height = height * tileHeight;
      buildingSprite.addChild(villa);
      totalHeight = villa.height;
      villa.zIndex = y * tileHeight - 1;
    }

    // 注册建筑信息
    sprite = buildingSprite;

    // 设置精灵位置 - 建筑底部对齐瓦片底部
    // 建筑右下角作为锚点，所以要移动到右下角位置
    sprite.x = Math.floor(x * tileWidth) + (width * tileWidth) - width * tileWidth +
      (buildingInfo.style === "house" ? 0.05 * sprite.width : 0); // 右边对齐，只有房屋类型+20

    // y坐标设置为建筑底部对齐地面
    // 这里使用buildingHeight表示建筑占用的格子数量
    sprite.y = Math.floor(y * tileHeight) + (height * tileHeight) - totalHeight +
      (buildingInfo.style === "house" ? 0.1 * totalHeight : 0) - 15;

    // 父精灵点击事件
    sprite.interactive = true;
    sprite.buttonMode = true;

    // 存储建筑尺寸和位置信息
    sprite.buildingGridX = x;
    sprite.buildingGridY = y;
    sprite.buildingGridWidth = width;
    sprite.buildingGridHeight = height;

    // 为建筑设置唯一ID，并存储相关信息
    const buildingId = `building_${buildingInfo.style}_${buildingInfo.type}_${x}_${y}`;
    sprite.buildingId = buildingId;

    // 注册建筑信息到BuildingRenderer
    this.buildingData[buildingId] = {
      id: buildingId,
      type: buildingInfo.type,
      style: buildingInfo.style,
      floors: buildingInfo.floors,
      width: width,
      height: height,
      x: x,
      y: y
    };

    // 创建建筑阴影
    let shadow = null;
    if (buildingInfo.style === "house") {
      shadow = this.createBuildingShadow(sprite, x, y, width, height, tileWidth, tileHeight, floors);
    }

    return {
      sprite,
      buildingId,
      shadow
    };
  }

  createBuildingShadow(sprite, x, y, width, height, tileWidth, tileHeight, floors) {
    // 创建一个新的容器作为阴影
    let shadow = new PIXI.Container();

    // 检查sprite是否是Container且有子精灵
    if (sprite.children && sprite.children.length > 0) {
      // 复制整个建筑的所有组件来创建完整阴影
      for (let i = 0; i < sprite.children.length; i++) {
        const childSprite = sprite.children[i];
        const shadowPart = new PIXI.Sprite(childSprite.texture);

        // 复制原始子精灵的属性
        shadowPart.width = childSprite.width;
        shadowPart.height = childSprite.height;
        shadowPart.x = childSprite.x;
        shadowPart.y = childSprite.y;

        // 创建颜色过滤器，将精灵变为黑色
        const colorMatrix = new PIXI.ColorMatrixFilter();
        colorMatrix.blackAndWhite(true);
        colorMatrix.brightness(0, false);

        // 应用过滤器
        shadowPart.filters = [colorMatrix];

        // 添加到阴影容器
        shadow.addChild(shadowPart);
      }

      // 设置整体容器的属性
      shadow.width = sprite.width;
      shadow.height = sprite.height;
    } else {
      // 如果不是Container，直接创建一个精灵
      shadow = new PIXI.Sprite(sprite.texture);
      shadow.width = sprite.width;
      shadow.height = sprite.height;

      // 创建颜色过滤器
      const colorMatrix = new PIXI.ColorMatrixFilter();
      colorMatrix.blackAndWhite(true);
      colorMatrix.brightness(0, false);

      // 应用过滤器
      shadow.filters = [colorMatrix];
    }

    // 设置透明度
    shadow.alpha = 0.4;

    // 设置阴影高度为原始高度的30%
    shadow.scale.y = 0.3;

    // 设置旋转角度为90度，使阴影水平
    // shadow.rotation = Math.PI / 2; // 90度旋转

    // 设置阴影位置，模拟左上方光源
    // 阴影位于建筑右侧
    shadow.x = sprite.x + sprite.width / 2;
    shadow.y = sprite.y + sprite.height - shadow.height;
    shadow.zIndex = sprite.y - 2;

    return shadow;
  }

  /**
   * 获取建筑信息
   * @param {string} buildingId 建筑ID
   * @returns {Object} 建筑数据对象
   */
  getBuildingData(buildingId) {
    // 先尝试从gameStore获取建筑数据
    const gameStore = this.ensureGameStore();
    if (gameStore) {
      const building = gameStore.getBuildingById(buildingId);
      if (building) {
        return building;
      }
    }
    
    // 如果没有从gameStore获取到，则从本地缓存获取
    if (!buildingId) {
      console.warn(`获取建筑数据失败: 无效的建筑ID`);
      return null;
    }

    const data = this.buildingData[buildingId];

    if (!data) {
      console.warn(`找不到ID为${buildingId}的建筑数据`);
      return null;
    }
    
    return data;
  }
  
  /**
   * 根据坐标获取建筑
   * @param {number} x 网格X坐标
   * @param {number} y 网格Y坐标
   * @returns {Object} 建筑对象
   */
  getBuildingAtCoordinates(x, y) {
    // 尝试从gameStore获取建筑数据
    const gameStore = this.ensureGameStore();
    if (gameStore) {
      return gameStore.getBuildingByCoordinates(x, y);
    }
    
    // 如果无法从gameStore获取，返回null
    return null;
  }

  /**
   * 清理纹理缓存
   */
  clearTextures() {
    // 销毁所有纹理
    for (const key in this.buildingTextures) {
      if (this.buildingTextures[key]) {
        this.buildingTextures[key].destroy(true);
      }
    }
    // 清空纹理缓存
    this.buildingTextures = {};
    this.textures = {}; // 同时清理兼容属性

    // 清空楼层数缓存
    this.floorCountCache = {};

    // 清空建筑数据
    this.buildingData = {};

    // 重置建筑计数
    this.buildingCounter = 0;
    
    // 如果有gameStore，清空其中的建筑数据
    const gameStore = this.ensureGameStore();
    if (gameStore) {
      gameStore.clearBuildings();
    }
  }
}

export default BuildingRenderer; 