/**
 * 道路绘制组件
 * 用于使用PIXI绘制城市道路网络
 */
import * as PIXI from 'pixi.js';

class RoadRenderer {
  constructor() {
    this.roadTextures = {}; // 缓存生成的道路纹理
    this.roadNetworkData = {}; // 存储道路网络的额外数据
    this.roadNodeCounter = 0; // 用于生成唯一道路节点ID的计数器
    this.initializeStyles();
  }

  /**
   * 初始化各种道路风格
   */
  initializeStyles() {
    // 定义像素风格道路样式库
    this.styles = {
      // 道路类型
      roadTypes: {
        // 基础道路（默认使用垂直方向）
        "road": {
          roadColor: 0x444444, // 深灰色路面
          linesColor: 0xFFFFFF, // 白色路线
          edgeColor: 0x222222, // 道路边缘
          grassColor: 0x3CB371, // 草地/绿化带颜色
          pixelSize: 4 // 像素尺寸
        },
        // 横向道路
        "road_horizontal": {
          roadColor: 0x444444,
          linesColor: 0xFFFFFF,
          edgeColor: 0x222222,
          grassColor: 0x3CB371,
          pixelSize: 4
        },
        // 纵向道路
        "road_vertical": {
          roadColor: 0x444444,
          linesColor: 0xFFFFFF,
          edgeColor: 0x222222,
          grassColor: 0x3CB371,
          pixelSize: 4
        },
        // 十字路口
        "road_crossroad": {
          roadColor: 0x444444,
          linesColor: 0xFFFFFF,
          edgeColor: 0x222222,
          grassColor: 0x3CB371,
          crosswalkColor: 0xFFFFFF,
          pixelSize: 4
        }
      }
    };
  }

  /**
   * 创建道路纹理
   * @param {string} roadType 道路类型
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {PIXI.Application} app PIXI应用
   * @returns {PIXI.Texture} 生成的道路纹理
   */
  createRoadTexture(roadType, tileWidth, tileHeight, app) {
    // 检查缓存
    const cacheKey = `${roadType}_${tileWidth}_${tileHeight}`;
    if (this.roadTextures[cacheKey]) {
      return this.roadTextures[cacheKey];
    }

    // 创建图形对象进行绘制
    const graphics = new PIXI.Graphics();
    
    // 获取道路样式
    const style = this.styles.roadTypes[roadType] || this.styles.roadTypes["road"];
    const pixelSize = style.pixelSize;
    
    // 绘制像素风格的道路
    this.drawPixelRoad(graphics, roadType, tileWidth, tileHeight, style);
    
    // 从Graphics对象生成纹理
    const canvas = app.renderer.extract.canvas(graphics);
    const texture = PIXI.Texture.from(canvas);
    
    // 缓存纹理
    this.roadTextures[cacheKey] = texture;
    
    return texture;
  }

  /**
   * 绘制像素风格的道路
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {string} roadType 道路类型
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {Object} style 道路样式
   */
  drawPixelRoad(graphics, roadType, tileWidth, tileHeight, style) {
    const pixelSize = style.pixelSize;
    const pxWidth = Math.floor(tileWidth / pixelSize);
    const pxHeight = Math.floor(tileHeight / pixelSize);
    
    // 先绘制草地/背景
    this.drawPixelBackground(graphics, pxWidth, pxHeight, pixelSize, style);
    
    // 根据道路类型绘制不同的道路
    switch (roadType) {
      case "road_horizontal":
        this.drawHorizontalRoad(graphics, pxWidth, pxHeight, pixelSize, style);
        break;
      case "road_vertical":
        this.drawVerticalRoad(graphics, pxWidth, pxHeight, pixelSize, style);
        break;
      case "road_crossroad":
        this.drawCrossroad(graphics, pxWidth, pxHeight, pixelSize, style);
        break;
      default:
        // 默认为垂直道路
        this.drawVerticalRoad(graphics, pxWidth, pxHeight, pixelSize, style);
    }
  }

  /**
   * 绘制像素背景（草地/绿化带）
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {number} pxWidth 像素宽度
   * @param {number} pxHeight 像素高度
   * @param {number} pixelSize 像素尺寸
   * @param {Object} style 道路样式
   */
  drawPixelBackground(graphics, pxWidth, pxHeight, pixelSize, style) {
    // 绘制背景
    graphics.fill({ color: style.grassColor });
    graphics.rect(0, 0, pxWidth * pixelSize, pxHeight * pixelSize);
    
    // 随机添加一些深浅不一的草丛，增加像素风格的纹理感
    const darkGrass = 0x2E8B57; // 深绿色
    const lightGrass = 0x66CDAA; // 浅绿色
    
    // 添加随机深色草丛
    for (let i = 0; i < pxWidth * pxHeight / 10; i++) {
      const x = Math.floor(Math.random() * pxWidth);
      const y = Math.floor(Math.random() * pxHeight);
      graphics.fill({ color: darkGrass });
      graphics.rect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
    }
    
    // 添加随机浅色草丛
    for (let i = 0; i < pxWidth * pxHeight / 15; i++) {
      const x = Math.floor(Math.random() * pxWidth);
      const y = Math.floor(Math.random() * pxHeight);
      graphics.fill({ color: lightGrass });
      graphics.rect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
    }
  }
  
  /**
   * 绘制水平方向的像素道路
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {number} pxWidth 像素宽度
   * @param {number} pxHeight 像素高度
   * @param {number} pixelSize 像素尺寸
   * @param {Object} style 道路样式
   */
  drawHorizontalRoad(graphics, pxWidth, pxHeight, pixelSize, style) {
    const roadHeight = Math.floor(pxHeight / 2); // 道路占据中间一半高度
    const startY = Math.floor(pxHeight / 4); // 从1/4处开始
    
    // 绘制道路主体
    graphics.fill({ color: style.roadColor });
    graphics.rect(0, startY * pixelSize, pxWidth * pixelSize, roadHeight * pixelSize);
    
    // 绘制道路边缘
    graphics.fill({ color: style.edgeColor });
    graphics.rect(0, startY * pixelSize, pxWidth * pixelSize, pixelSize);
    graphics.rect(0, (startY + roadHeight - 1) * pixelSize, pxWidth * pixelSize, pixelSize);
    
    // 绘制中心虚线
    const centerY = startY + Math.floor(roadHeight / 2);
    for (let x = 1; x < pxWidth; x += 3) {
      graphics.fill({ color: style.linesColor });
      graphics.rect(x * pixelSize, centerY * pixelSize, 2 * pixelSize, pixelSize);
    }
    
    // 添加一些随机的路面细节（小坑洼或纹理）
    this.addRoadDetails(graphics, 0, startY, pxWidth, roadHeight, pixelSize, style);
  }
  
  /**
   * 绘制垂直方向的像素道路
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {number} pxWidth 像素宽度
   * @param {number} pxHeight 像素高度
   * @param {number} pixelSize 像素尺寸
   * @param {Object} style 道路样式
   */
  drawVerticalRoad(graphics, pxWidth, pxHeight, pixelSize, style) {
    const roadWidth = Math.floor(pxWidth / 2); // 道路占据中间一半宽度
    const startX = Math.floor(pxWidth / 4); // 从1/4处开始
    
    // 绘制道路主体
    graphics.fill({ color: style.roadColor });
    graphics.rect(startX * pixelSize, 0, roadWidth * pixelSize, pxHeight * pixelSize);
    
    // 绘制道路边缘
    graphics.fill({ color: style.edgeColor });
    graphics.rect(startX * pixelSize, 0, pixelSize, pxHeight * pixelSize);
    graphics.rect((startX + roadWidth - 1) * pixelSize, 0, pixelSize, pxHeight * pixelSize);
    
    // 绘制中心虚线
    const centerX = startX + Math.floor(roadWidth / 2);
    for (let y = 1; y < pxHeight; y += 3) {
      graphics.fill({ color: style.linesColor });
      graphics.rect(centerX * pixelSize, y * pixelSize, pixelSize, 2 * pixelSize);
    }
    
    // 添加一些随机的路面细节（小坑洼或纹理）
    this.addRoadDetails(graphics, startX, 0, roadWidth, pxHeight, pixelSize, style);
  }
  
  /**
   * 绘制十字路口
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {number} pxWidth 像素宽度
   * @param {number} pxHeight 像素高度
   * @param {number} pixelSize 像素尺寸
   * @param {Object} style 道路样式
   */
  drawCrossroad(graphics, pxWidth, pxHeight, pixelSize, style) {
    const roadWidth = Math.floor(pxWidth / 2);
    const roadHeight = Math.floor(pxHeight / 2);
    const startX = Math.floor(pxWidth / 4);
    const startY = Math.floor(pxHeight / 4);
    
    // 绘制十字路口主体
    graphics.fill({ color: style.roadColor });
    
    // 水平道路
    graphics.rect(0, startY * pixelSize, pxWidth * pixelSize, roadHeight * pixelSize);
    
    // 垂直道路
    graphics.rect(startX * pixelSize, 0, roadWidth * pixelSize, pxHeight * pixelSize);
    
    // 绘制道路边缘
    graphics.fill({ color: style.edgeColor });
    
    // 上边缘
    graphics.rect(startX * pixelSize, 0, roadWidth * pixelSize, pixelSize);
    
    // 下边缘
    graphics.rect(startX * pixelSize, (pxHeight - 1) * pixelSize, roadWidth * pixelSize, pixelSize);
    
    // 左边缘
    graphics.rect(0, startY * pixelSize, pixelSize, roadHeight * pixelSize);
    
    // 右边缘
    graphics.rect((pxWidth - 1) * pixelSize, startY * pixelSize, pixelSize, roadHeight * pixelSize);
    
    // 绘制人行横道
    this.drawPixelCrosswalks(graphics, pxWidth, pxHeight, pixelSize, startX, startY, roadWidth, roadHeight, style);
    
    // 添加一些随机的路面细节
    this.addRoadDetails(graphics, 0, startY, pxWidth, roadHeight, pixelSize, style);
    this.addRoadDetails(graphics, startX, 0, roadWidth, pxHeight, pixelSize, style);
  }
  
  /**
   * 绘制像素风格的人行横道
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {number} pxWidth 像素宽度
   * @param {number} pxHeight 像素高度
   * @param {number} pixelSize 像素尺寸
   * @param {number} startX 道路起始X坐标（像素单位）
   * @param {number} startY 道路起始Y坐标（像素单位）
   * @param {number} roadWidth 道路宽度（像素单位）
   * @param {number} roadHeight 道路高度（像素单位）
   * @param {Object} style 道路样式
   */
  drawPixelCrosswalks(graphics, pxWidth, pxHeight, pixelSize, startX, startY, roadWidth, roadHeight, style) {
    const crosswalkWidth = 4;
    
    // 绘制上方人行横道
    for (let i = 0; i < crosswalkWidth; i += 2) {
      for (let x = startX + 2; x < startX + roadWidth - 2; x += 2) {
        graphics.fill({ color: style.crosswalkColor });
        graphics.rect(x * pixelSize, (startY - 2 - i) * pixelSize, pixelSize, pixelSize);
      }
    }
    
    // 绘制下方人行横道
    for (let i = 0; i < crosswalkWidth; i += 2) {
      for (let x = startX + 2; x < startX + roadWidth - 2; x += 2) {
        graphics.fill({ color: style.crosswalkColor });
        graphics.rect(x * pixelSize, (startY + roadHeight + 1 + i) * pixelSize, pixelSize, pixelSize);
      }
    }
    
    // 绘制左侧人行横道
    for (let i = 0; i < crosswalkWidth; i += 2) {
      for (let y = startY + 2; y < startY + roadHeight - 2; y += 2) {
        graphics.fill({ color: style.crosswalkColor });
        graphics.rect((startX - 2 - i) * pixelSize, y * pixelSize, pixelSize, pixelSize);
      }
    }
    
    // 绘制右侧人行横道
    for (let i = 0; i < crosswalkWidth; i += 2) {
      for (let y = startY + 2; y < startY + roadHeight - 2; y += 2) {
        graphics.fill({ color: style.crosswalkColor });
        graphics.rect((startX + roadWidth + 1 + i) * pixelSize, y * pixelSize, pixelSize, pixelSize);
      }
    }
  }
  
  /**
   * 添加路面细节（裂缝、不平整等）
   * @param {PIXI.Graphics} graphics 图形对象
   * @param {number} startX 起始X坐标（像素单位）
   * @param {number} startY 起始Y坐标（像素单位）
   * @param {number} width 宽度（像素单位）
   * @param {number} height 高度（像素单位）
   * @param {number} pixelSize 像素尺寸
   * @param {Object} style 道路样式
   */
  addRoadDetails(graphics, startX, startY, width, height, pixelSize, style) {
    // 路面暗色斑点（坑洼或修补）
    const darkSpotColor = 0x333333;
    const lightSpotColor = 0x555555;
    
    // 添加随机深色斑点
    for (let i = 0; i < width * height / 20; i++) {
      const x = startX + Math.floor(Math.random() * width);
      const y = startY + Math.floor(Math.random() * height);
      
      // 确保在道路范围内
      if (x >= startX && x < startX + width && y >= startY && y < startY + height) {
        graphics.fill({ color: darkSpotColor });
        graphics.rect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
      }
    }
    
    // 添加随机浅色斑点
    for (let i = 0; i < width * height / 25; i++) {
      const x = startX + Math.floor(Math.random() * width);
      const y = startY + Math.floor(Math.random() * height);
      
      // 确保在道路范围内
      if (x >= startX && x < startX + width && y >= startY && y < startY + height) {
        graphics.fill({ color: lightSpotColor });
        graphics.rect(x * pixelSize, y * pixelSize, pixelSize, pixelSize);
      }
    }
  }

  /**
   * 创建道路精灵
   * @param {string} roadType 道路类型
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {PIXI.Application} app PIXI应用
   * @returns {PIXI.Sprite} 道路精灵
   */
  createRoadSprite(roadType, tileWidth, tileHeight, app) {
    // 获取或创建道路纹理
    const texture = this.createRoadTexture(roadType, tileWidth, tileHeight, app);
    
    // 创建精灵
    const sprite = new PIXI.Sprite(texture);
    
    // 为道路节点生成唯一ID
    const roadNodeId = `road_node_${this.roadNodeCounter++}`;
    sprite.roadNodeId = roadNodeId;
    
    // 存储道路节点数据
    this.roadNetworkData[roadNodeId] = {
      id: roadNodeId,
      type: roadType,
      connections: this.getRoadConnections(roadType)
    };
    
    return sprite;
  }

  /**
   * 根据道路类型获取连接方向
   * @param {string} roadType 道路类型
   * @returns {Object} 包含上下左右四个方向是否连接的对象
   */
  getRoadConnections(roadType) {
    // 默认所有方向不连接
    const connections = {
      top: false,
      right: false,
      bottom: false,
      left: false
    };
    
    // 根据道路类型设置连接
    switch (roadType) {
      case "road_vertical":
        connections.top = true;
        connections.bottom = true;
        break;
        
      case "road_horizontal":
        connections.left = true;
        connections.right = true;
        break;
        
      case "road_crossroad":
        connections.top = true;
        connections.right = true;
        connections.bottom = true;
        connections.left = true;
        break;
        
      default:
        // 基础道路默认为垂直
        if (roadType === "road") {
          connections.top = true;
          connections.bottom = true;
        }
    }
    
    return connections;
  }

  /**
   * 获取道路节点数据
   * @param {string} roadNodeId 道路节点ID
   * @returns {Object|null} 道路节点数据，如果未找到则返回null
   */
  getRoadNodeData(roadNodeId) {
    return this.roadNetworkData[roadNodeId] || null;
  }

  /**
   * 判断两个坐标点是否通过道路连接
   * @param {number} x1 第一个点的X坐标
   * @param {number} y1 第一个点的Y坐标
   * @param {number} x2 第二个点的X坐标
   * @param {number} y2 第二个点的Y坐标
   * @param {Array} roadLayerData 道路层数据
   * @param {number} mapWidth 地图宽度
   * @returns {boolean} 如果两点通过道路连接则返回true，否则返回false
   */
  arePointsConnectedByRoad(x1, y1, x2, y2, roadLayerData, mapWidth) {
    // 获取第一个点的道路ID
    const tileIndex1 = y1 * mapWidth + x1;
    const roadId1 = roadLayerData[tileIndex1];
    
    // 获取第二个点的道路ID
    const tileIndex2 = y2 * mapWidth + x2;
    const roadId2 = roadLayerData[tileIndex2];
    
    // 如果任一点不是道路，则不连接
    if (roadId1 === 0 || roadId2 === 0) {
      return false;
    }
    
    // 如果两点相邻，需要检查它们的连接方向
    if (
      (Math.abs(x1 - x2) === 1 && y1 === y2) || // 横向相邻
      (Math.abs(y1 - y2) === 1 && x1 === x2)    // 纵向相邻
    ) {
      // 获取两个道路节点的连接信息
      const node1 = this.roadNetworkData[`road_node_${x1}_${y1}`];
      const node2 = this.roadNetworkData[`road_node_${x2}_${y2}`];
      
      if (!node1 || !node2) return false;
      
      // 确定两点之间的方向
      let direction1to2;
      if (x2 > x1) direction1to2 = 'right';
      else if (x2 < x1) direction1to2 = 'left';
      else if (y2 > y1) direction1to2 = 'bottom';
      else direction1to2 = 'top';
      
      // 确定从点2到点1的反方向
      let direction2to1;
      if (direction1to2 === 'right') direction2to1 = 'left';
      else if (direction1to2 === 'left') direction2to1 = 'right';
      else if (direction1to2 === 'bottom') direction2to1 = 'top';
      else direction2to1 = 'bottom';
      
      // 检查两个节点的连接是否都指向对方
      return node1.connections[direction1to2] && node2.connections[direction2to1];
    }
    
    return false;
  }

  /**
   * 清理纹理资源
   */
  clearTextures() {
    Object.values(this.roadTextures).forEach(texture => {
      if (texture) {
        texture.destroy(true);
      }
    });
    this.roadTextures = {};
  }

  /**
   * 分析道路网络结构，构建导航图
   * @param {Array} roadLayerData 道路层数据
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @returns {Object} 导航图数据
   */
  analyzeRoadNetwork(roadLayerData, mapWidth, mapHeight) {
    console.log('开始分析道路网络...');
    
    // 导航图对象，用于存储节点和连接信息
    const navigationGraph = {
      nodes: {}, // 存储节点信息: {id: {x, y, connections: []}}
      junctions: [], // 存储路口信息
      segments: []  // 存储道路段信息
    };
    
    // 查找所有道路节点
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const tileIndex = y * mapWidth + x;
        const roadId = roadLayerData[tileIndex];
        
        if (roadId !== 0) {
          // 发现道路节点
          const nodeId = `${x}_${y}`;
           
          // 确定节点类型
          const roadNodeType = this.determineRoadNodeType(x, y, roadLayerData, mapWidth, mapHeight);
          
          // 存储节点信息
          navigationGraph.nodes[nodeId] = {
            id: nodeId,
            x: x,
            y: y,
            type: roadNodeType,
            connections: []
          };
          
          // 如果是路口(十字路口)，加入路口列表
          if (roadNodeType === 'road_crossroad') {
            navigationGraph.junctions.push(nodeId);
          }
        }
      }
    }
    
    // 建立节点之间的连接关系
    const nodeIds = Object.keys(navigationGraph.nodes);
    
    // 遍历所有节点，找出它们之间的连接
    for (let i = 0; i < nodeIds.length; i++) {
      const nodeId = nodeIds[i];
      const node = navigationGraph.nodes[nodeId];
      
      // 检查四个方向上的连接
      this.checkNodeConnections(node, navigationGraph, roadLayerData, mapWidth, mapHeight);
    }
    
    // 识别道路段
    this.identifyRoadSegments(navigationGraph);
    
    console.log(`道路网络分析完成: ${nodeIds.length} 个节点, ${navigationGraph.junctions.length} 个路口, ${navigationGraph.segments.length} 条道路段`);
    
    return navigationGraph;
  }

  /**
   * 确定道路节点类型
   * @param {number} x 节点X坐标
   * @param {number} y 节点Y坐标
   * @param {Array} roadLayerData 道路层数据
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @returns {string} 节点类型
   */
  determineRoadNodeType(x, y, roadLayerData, mapWidth, mapHeight) {
    // 检查上下左右四个方向是否有道路
    const hasTopRoad = y > 0 && roadLayerData[(y - 1) * mapWidth + x] !== 0;
    const hasRightRoad = x < mapWidth - 1 && roadLayerData[y * mapWidth + (x + 1)] !== 0;
    const hasBottomRoad = y < mapHeight - 1 && roadLayerData[(y + 1) * mapWidth + x] !== 0;
    const hasLeftRoad = x > 0 && roadLayerData[y * mapWidth + (x - 1)] !== 0;
    
    // 计算连接的方向数量
    const connectionCount = (hasTopRoad ? 1 : 0) + (hasRightRoad ? 1 : 0) + 
                             (hasBottomRoad ? 1 : 0) + (hasLeftRoad ? 1 : 0);
    
    // 检查是否为地图边缘
    const isEdge = x === 0 || x === mapWidth - 1 || y === 0 || y === mapHeight - 1;
    
    // 根据连接方向确定节点类型
    if (connectionCount >= 3) {
      // 三个或四个方向都有连接 - 十字路口
      return 'road_crossroad';
    } else if (connectionCount === 2) {
      // 两个方向有连接
      if (hasTopRoad && hasBottomRoad) {
        // 上下连通 - 垂直道路
        return 'road_vertical';
      } else if (hasLeftRoad && hasRightRoad) {
        // 左右连通 - 水平道路
        return 'road_horizontal';
      } else {
        // 拐角 - 使用十字路口表示所有转弯
        return 'road_crossroad';
      }
    } else if (connectionCount === 1) {
      // 只有一个方向连接 - 路的尽头
      // 如果在地图边缘，也使用十字路口，保证连接性
      if (isEdge) {
        return 'road_crossroad';
      }
      
      if (hasTopRoad || hasBottomRoad) {
        return 'road_vertical';
      } else {
        return 'road_horizontal';
      }
    }
    
    // 默认返回十字路口类型，确保边缘连接
    if (isEdge) {
      return 'road_crossroad';
    }
    
    // 默认返回垂直道路类型
    return 'road_vertical';
  }

  /**
   * 检查节点的连接关系
   * @param {Object} node 要检查的节点
   * @param {Object} navigationGraph 导航图
   * @param {Array} roadLayerData 道路层数据
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   */
  checkNodeConnections(node, navigationGraph, roadLayerData, mapWidth, mapHeight) {
    const { x, y } = node;
    const directions = [
      { dx: 0, dy: -1, name: 'top' },    // 上
      { dx: 1, dy: 0, name: 'right' },   // 右
      { dx: 0, dy: 1, name: 'bottom' },  // 下
      { dx: -1, dy: 0, name: 'left' }    // 左
    ];
    
    // 获取节点连接信息
    const connections = this.getRoadConnections(node.type);
    
    // 检查每个可能的连接方向
    for (const dir of directions) {
      const dirName = dir.name;
      
      // 如果该方向可连接
      if (connections[dirName]) {
        let nx = x + dir.dx;
        let ny = y + dir.dy;
        
        // 检查该方向是否有道路，并找到直接相连的节点
        while (nx >= 0 && nx < mapWidth && ny >= 0 && ny < mapHeight) {
          const neighborIndex = ny * mapWidth + nx;
          const neighborId = `${nx}_${ny}`;
          
          // 如果找到另一个节点，建立连接
          if (roadLayerData[neighborIndex] !== 0 && navigationGraph.nodes[neighborId]) {
            // 计算距离（曼哈顿距离）
            const distance = Math.abs(nx - x) + Math.abs(ny - y);
            
            // 添加连接关系
            node.connections.push({
              target: neighborId,
              direction: dirName,
              distance: distance
            });
            
            // 找到连接节点后不再继续寻找
            break;
          }
          
          // 沿方向继续搜索
          nx += dir.dx;
          ny += dir.dy;
        }
      }
    }
  }

  /**
   * 识别道路段
   * @param {Object} navigationGraph 导航图
   */
  identifyRoadSegments(navigationGraph) {
    // 已处理的节点集合
    const processedNodes = new Set();
    
    // 遍历所有节点
    for (const nodeId in navigationGraph.nodes) {
      if (processedNodes.has(nodeId)) continue;
      
      const node = navigationGraph.nodes[nodeId];
      processedNodes.add(nodeId);
      
      // 对每个连接方向，识别道路段
      for (const connection of node.connections) {
        const targetNodeId = connection.target;
        
        // 如果已处理过这条连接，跳过
        if (processedNodes.has(`${nodeId}-${targetNodeId}`)) continue;
        
        // 标记这条连接已处理
        processedNodes.add(`${nodeId}-${targetNodeId}`);
        processedNodes.add(`${targetNodeId}-${nodeId}`);
        
        // 创建道路段
        const segment = {
          id: `segment_${navigationGraph.segments.length}`,
          start: nodeId,
          end: targetNodeId,
          length: connection.distance,
          direction: connection.direction
        };
        
        // 添加到道路段列表
        navigationGraph.segments.push(segment);
      }
    }
  }
}

export default RoadRenderer;