/**
 * 地图生成模块
 * 根据设定的地图尺寸随机生成地形（地面、道路、建筑、装饰）
 * 输出符合Tiled格式的地图数据
 */
import { useGameStore } from '../../stores/gameStore';

class MapGenerator {
  constructor() {
    // 尝试初始化gameStore
    try {
      // 由于组合式API的限制，可能需要在组件中传入gameStore
      this.gameStore = null;
    } catch (error) {
      console.warn('MapGenerator: 无法在构造函数中使用useGameStore，将在方法中使用');
    }

    // 定义瓦片类型ID
    this.TILE_TYPES = {
      EMPTY: 0,      // 空瓦片
      GRASS: 1,
      DIRT: 2,
      // 道路类型：横向道路、纵向道路、十字路口
      ROAD_HORIZONTAL: 4,
      ROAD_VERTICAL: 5,
      ROAD_CROSSROAD: 6,
      // 楼房类型
      BUILDING_MEDIUM: 21, // 2x1建筑
      BUILDING_LARGE: 22,  // 2x2建筑
      BUILDING_EXTRA_LARGE: 23, // 3x3建筑
      BUILDING_4X4: 24,    // 4x4建筑类型
      BUILDING_2X3: 25,    // 2x3建筑类型
      BUILDING_3X4: 26,    // 3x4建筑类型
      // 别墅类型
      VILLA_2X2: 27,    // 2x2别墅
      VILLA_3X2: 28,    // 3x2别墅
      VILLA_2X3: 29,    // 2x3别墅
      VILLA_3X3: 30,    // 3x3别墅
      // 装饰类型
      TREE: 40,          // 1x1 city
      BUSH: 41,         // 1x1 village
      TREE_LARGE: 42,     // 2x2 city
      GARDEN: 43,         // 2x2 village
      PARK: 44,           // 3x3 city
      FOUNTAIN: 45,       // 3x3 village
      EMPTY_1: 100,       // 1环
      EMPTY_2: 101,       // 2环
      EMPTY_3: 102,       // 3环
      EMPTY_4: 103,       // 4环
      EMPTY_5: 104        // 边缘区域 - 不生成建筑
    };

    // 定义建筑类型配置
    this.BUILDING_TYPE_CONFIG = {
      // 楼房类型配置
      [this.TILE_TYPES.BUILDING_MEDIUM]: {
        defaultFloors: 1,
        maxFloors: 3,
        width: 2,
        height: 1,
        style: "house"
      },
      [this.TILE_TYPES.BUILDING_LARGE]: {
        defaultFloors: 2,
        maxFloors: 4,
        width: 2,
        height: 2,
        style: "house"
      },
      [this.TILE_TYPES.BUILDING_2X3]: {
        defaultFloors: 3,
        maxFloors: 5,
        width: 2,
        height: 3,
        style: "house"
      },
      [this.TILE_TYPES.BUILDING_EXTRA_LARGE]: {
        defaultFloors: 3,
        maxFloors: 5,
        width: 3,
        height: 3,
        style: "house"
      },
      [this.TILE_TYPES.BUILDING_3X4]: {
        defaultFloors: 4,
        maxFloors: 4,
        width: 3,
        height: 4,
        style: "house"
      },
      [this.TILE_TYPES.BUILDING_4X4]: {
        defaultFloors: 4,
        maxFloors: 8,
        width: 4,
        height: 4,
        style: "house"
      },
      // 别墅类型配置
      [this.TILE_TYPES.VILLA_2X2]: {
        defaultFloors: 2,
        maxFloors: 2,
        width: 2,
        height: 2,
        style: "villa"
      },
      [this.TILE_TYPES.VILLA_3X2]: {
        defaultFloors: 2,
        maxFloors: 2,
        width: 3,
        height: 2,
        style: "villa"
      },
      [this.TILE_TYPES.VILLA_2X3]: {
        defaultFloors: 2,
        maxFloors: 2,
        width: 2,
        height: 3,
        style: "villa"
      },
      [this.TILE_TYPES.VILLA_3X3]: {
        defaultFloors: 2,
        maxFloors: 3,
        width: 3,
        height: 3,
        style: "villa"
      },
      // 装饰类型配置
      [this.TILE_TYPES.TREE]: {
        width: 1,
        height: 1,
        style: "decoration",
        type: "tree"
      },
      [this.TILE_TYPES.BUSH]: {
        width: 1,
        height: 1,
        style: "decoration",
        type: "bush"
      },
      [this.TILE_TYPES.TREE_LARGE]: {
        width: 2,
        height: 2,
        style: "decoration",
        type: "tree_large"
      },
      [this.TILE_TYPES.GARDEN]: {
        width: 2,
        height: 2,
        style: "decoration",
        type: "garden"
      },
      [this.TILE_TYPES.PARK]: {
        width: 3,
        height: 3,
        style: "decoration",
        type: "park"
      },
      [this.TILE_TYPES.FOUNTAIN]: {
        width: 3,
        height: 3,
        style: "decoration",
        type: "fountain"
      }
    };

    // 定义概率系数
    this.Probability = 1; // 基础概率为1

  }

  /**
   * 生成随机地图数据
   * @param {Object} options 地图生成选项
   * @param {number} options.width 地图宽度（瓦片数）
   * @param {number} options.height 地图高度（瓦片数）
   * @param {number} options.tileWidth 瓦片宽度（像素）
   * @param {number} options.tileHeight 瓦片高度（像素）
   * @param {number} options.population 城市人口总数
   * @returns {Object} 符合Tiled格式的地图数据
   */
  generate(options) {
    console.log('开始生成地图数据，配置:', options);
    const { width, height, tileWidth, tileHeight, population } = options;
    // 根据人口计算概率系数
    if (population < 5000) {
      this.Probability = 1;
    } else {
      // 每增加5000人口，概率增加0.5，最大到50000人口
      this.Probability = 1 + Math.min(Math.floor((population - 5000) / 5000) * 0.05, 9); // 最大值为10 (1 + 9)
    }
    console.log(`根据人口 ${population} 计算的概率系数: ${this.Probability}`);
    // 初始化四个图层
    const groundLayerData = new Array(width * height).fill(this.TILE_TYPES.GRASS);
    const roadLayerData = new Array(width * height).fill(this.TILE_TYPES.EMPTY);
    const sceneLayerData = new Array(width * height).fill(this.TILE_TYPES.EMPTY);
    const decorationLayerData = new Array(width * height).fill(this.TILE_TYPES.EMPTY);

    // 初始化建筑数据数组
    const buildings = [];

    // 1. 生成地面层 (先填充默认草地)
    this.generateGround(groundLayerData, width, height);

    // 2. 生成道路网络(初始道路类型为基础道路)
    this.generateRoads(roadLayerData, width, height);

    // 3. 识别道路类型，更新道路图层
    this.identifyRoadTypes(roadLayerData, width, height);

    // 4. 根据道路和环区调整地面
    this.adjustGroundBasedOnRoads(groundLayerData, roadLayerData, width, height);

    // 创建zoneLayer变量
    let zoneLayer;

    // 5. 在道路两侧生成建筑物，并获取zoneLayer
    const buildingResult = this.generateBuildings(sceneLayerData, roadLayerData, buildings, width, height);
    if (buildingResult && buildingResult.zoneLayer) {
      zoneLayer = buildingResult.zoneLayer;
    } else {
      // 如果generateBuildings没有返回zoneLayer，创建一个新的zoneLayer
      zoneLayer = new Array(width * height).fill(this.TILE_TYPES.EMPTY_5);
    }
    // 6. 在道路两侧空地上生成装饰物
    const decorations = this.generateDecorations(decorationLayerData, roadLayerData, sceneLayerData, zoneLayer, width, height, groundLayerData);

    // 7. 根据人口调整建筑高度 - 人口总数不能小于1000
    const minPopulation = this.gameStore.populationTotal;
    const adjustResult = this.adjustBuildingHeights(buildings, Math.max(minPopulation, population), width, height);

    // 如果需要增大地图尺寸
    if (adjustResult.needEnlarge) {
      console.log(`当前地图容量无法满足人口需求，增加地图尺寸并重新生成...`);
      // 增加地图尺寸
      options.width += 1;
      options.height += 1;
      console.log(`新地图尺寸: ${options.width} x ${options.height}`);
      // 递归调用generate生成更大的地图
      return this.generate(options);
    }

    // 统计各种瓦片的数量
    const tileCounts = this.countTiles(groundLayerData, roadLayerData, sceneLayerData, decorationLayerData);
    console.log('地图生成完成，瓦片统计:', tileCounts);


    // 打印地图层中的一些样本数据用于调试
    console.log('地图层样本数据:');
    console.log(`地面层(0,0): ${groundLayerData[0]}`);
    console.log(`道路层(10,10): ${roadLayerData[10 * width + 10]}`);
    console.log(`建筑层(12,12): ${sceneLayerData[12 * width + 12]}`);

    // 返回符合Tiled格式的地图数据
    return {
      tileWidth,
      tileHeight,
      width,
      height,
      layers: [
        {
          name: "Ground",
          type: "tilelayer",
          data: groundLayerData
        },
        {
          name: "Roads",
          type: "tilelayer",
          data: roadLayerData
        },
        {
          name: "Buildings",
          type: "tilelayer",
          data: sceneLayerData
        },
        {
          name: "Decorations",
          type: "tilelayer",
          data: decorationLayerData
        }
      ],
      buildingData: buildings, // 添加建筑数据
      decorationData: decorations, // 添加装饰物数据
      population: Math.max(minPopulation, population), // 添加人口数据
      zoneLayer: zoneLayer // 添加环区数据用于determineZoneType函数
    };
  }

  /**
   * 生成地面层
   * @param {Array} groundLayer 地面层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  generateGround(groundLayer, width, height) {
    // 初始化为草地
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        groundLayer[y * width + x] = this.TILE_TYPES.GRASS;
      }
    }
  }

  /**
   * 根据道路和环区调整地面
   * @param {Array} groundLayer 地面层数据
   * @param {Array} roadLayer 道路层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  adjustGroundBasedOnRoads(groundLayer, roadLayer, width, height) {
    // 计算地图中心点
    const centerX = Math.floor(width / 2);
    const centerY = Math.floor(height / 2);

    // 计算从中心到最远角落的距离（用于确定环的边界）
    const maxDistance = Math.sqrt(Math.pow(Math.max(centerX, width - centerX), 2) +
      Math.pow(Math.max(centerY, height - centerY), 2));

    // 设置1环和3环的边界半径
    const zone1Radius = maxDistance * 0.25; // 内环占25%
    const zone3Radius = maxDistance * 0.45; // 三环占65%

    // 根据环区和道路调整地面
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // 计算当前点到中心的距离
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));

        // 1环内所有地面都是DIRT
        if (distance <= zone1Radius) {
          groundLayer[y * width + x] = this.TILE_TYPES.DIRT;
        }
        // 检查是否是道路
        else if (roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY) {
          // 跳过处理，道路已在道路图层
          continue;
        }
        // 所有道路两侧都是DIRT，无论在哪个环区
        else {
          // 检查周围4个方向是否有道路
          const hasNearbyRoad = this.checkForNearbyRoad(roadLayer, x, y, width, height);

          // 如果是道路两侧的地块，设置为DIRT
          if (hasNearbyRoad) {
            groundLayer[y * width + x] = this.TILE_TYPES.DIRT;
          }
        }
        // 其他区域保持草地(已在初始化时设置)
      }
    }
  }

  /**
   * 检查周围是否有道路
   * @param {Array} roadLayer 道路层数据
   * @param {number} x 坐标x
   * @param {number} y 坐标y
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @returns {boolean} 是否有道路
   */
  checkForNearbyRoad(roadLayer, x, y, width, height) {
    // 检查上下左右四个方向
    const directions = [
      { dx: -1, dy: 0 }, // 左
      { dx: 1, dy: 0 },  // 右
      { dx: 0, dy: -1 }, // 上
      { dx: 0, dy: 1 }   // 下
    ];

    for (const dir of directions) {
      const checkX = x + dir.dx;
      const checkY = y + dir.dy;

      // 确保检查的位置在地图范围内
      if (checkX >= 0 && checkX < width && checkY >= 0 && checkY < height) {
        // 检查该位置是否是道路
        if (roadLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * 生成道路网络
   * @param {Array} roadLayer 道路层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  generateRoads(roadLayer, width, height) {
    // 生成主要道路（简单的网格形式）
    const roadSpacing = 15 + Math.floor(Math.random() * 3); // 主干道间距随机在15-17之间

    // 计算地图中心点
    const centerX = Math.floor(width / 2);
    const centerY = Math.floor(height / 2);

    // 计算从中心到最远角落的距离（用于确定环的边界）
    const maxDistance = Math.sqrt(Math.pow(Math.max(centerX, width - centerX), 2) +
      Math.pow(Math.max(centerY, height - centerY), 2));

    // 设置4环的边界半径
    const zone4Radius = maxDistance * 0.65; // 内环+二环+三环+四环占85%

    // 固定边缘区域宽度为6格
    const edgeWidth = 6;

    // 判断一个点是否在无人区(EMPTY_5)
    const isInEmpty5Zone = (x, y) => {
      // 检查是否在边缘6格内
      if (x < edgeWidth || y < edgeWidth || x >= width - edgeWidth || y >= height - edgeWidth) {
        return true;
      }
      
      // 检查是否在4环外
      const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
      return distance > zone4Radius;
    };

    // 水平主干道
    const horizontalMajorRoads = [];
    // 确保地图中心附近有道路，起始位置随机在8-12之间
    const startY = 8 + Math.floor(Math.random() * 5);
    for (let y = startY; y < height; y += roadSpacing) {
      if (y < height) {
        horizontalMajorRoads.push(y);
        for (let x = 0; x < width; x++) {
          roadLayer[y * width + x] = this.TILE_TYPES.ROAD;
        }
      }
    }

    // 垂直主干道
    const verticalMajorRoads = [];
    // 确保地图中心附近有道路，起始位置随机在8-12之间
    const startX = 8 + Math.floor(Math.random() * 5);
    for (let x = startX; x < width; x += roadSpacing) {
      if (x < width) {
        verticalMajorRoads.push(x);
        for (let y = 0; y < height; y++) {
          roadLayer[y * width + x] = this.TILE_TYPES.ROAD;
        }
      }
    }

    // 记录已生成的垂直次级道路位置
    const verticalSecondaryRoads = [];

    // 从水平主干道生成垂直次级道路
    for (const majorY of horizontalMajorRoads) {
      // 每隔4-6格生成一条次级道路，原来是3-5
      for (let x = 5; x < width; x += 4 + Math.floor(Math.random() * 3)) {
        // 确保与主干道保持至少4格距离，原来是3
        if (verticalMajorRoads.some(majorX => Math.abs(majorX - x) < 4)) {
          continue;
        }

        // 确保与其他次级道路保持至少4格距离，原来是3
        if (verticalSecondaryRoads.some(secX => Math.abs(secX - x) < 4)) {
          continue;
        }

        // 记录新的次级道路位置
        verticalSecondaryRoads.push(x);

        // 向上延伸
        for (let y = majorY; y >= 0; y--) {
          // 如果在无人区，不生成次级道路
          if (isInEmpty5Zone(x, y)) {
            continue;
          }
          roadLayer[y * width + x] = this.TILE_TYPES.ROAD;
        }

        // 向下延伸
        for (let y = majorY; y < height; y++) {
          // 如果在无人区，不生成次级道路
          if (isInEmpty5Zone(x, y)) {
            continue;
          }
          roadLayer[y * width + x] = this.TILE_TYPES.ROAD;
        }
      }
    }

    // 记录已生成的水平次级道路位置
    const horizontalSecondaryRoads = [];

    // 从垂直主干道生成水平次级道路
    for (const majorX of verticalMajorRoads) {
      // 每隔4-6格生成一条次级道路，原来是3-5
      for (let y = 5; y < height; y += 4 + Math.floor(Math.random() * 3)) {
        // 确保与主干道保持至少4格距离，原来是3
        if (horizontalMajorRoads.some(majorY => Math.abs(majorY - y) < 4)) {
          continue;
        }

        // 确保与其他次级道路保持至少4格距离，原来是3
        if (horizontalSecondaryRoads.some(secY => Math.abs(secY - y) < 4)) {
          continue;
        }

        // 记录新的次级道路位置
        horizontalSecondaryRoads.push(y);

        // 向左延伸
        for (let x = majorX; x >= 0; x--) {
          // 如果在无人区，不生成次级道路
          if (isInEmpty5Zone(x, y)) {
            continue;
          }
          roadLayer[y * width + x] = this.TILE_TYPES.ROAD;
        }

        // 向右延伸
        for (let x = majorX; x < width; x++) {
          // 如果在无人区，不生成次级道路
          if (isInEmpty5Zone(x, y)) {
            continue;
          }
          roadLayer[y * width + x] = this.TILE_TYPES.ROAD;
        }
      }
    }

    // 检查并移除任何间隔小于4格的并行道路，原来是3
    this.removeCloseParallelRoads(roadLayer, width, height);
    
    // 清除没有两端连接到十字路口的次级道路
    this.removeDeadEndRoads(roadLayer, width, height, horizontalMajorRoads, verticalMajorRoads);
  }
  
  /**
   * 移除没有两端都连接到十字路口的次级道路
   * @param {Array} roadLayer 道路层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @param {Array} horizontalMajorRoads 水平主干道位置数组
   * @param {Array} verticalMajorRoads 垂直主干道位置数组
   */
  removeDeadEndRoads(roadLayer, width, height, horizontalMajorRoads, verticalMajorRoads) {
    console.log("清除没有两端连接到十字路口的次级道路");
    
    // 创建一个临时数组来存储哪些道路需要保留
    const tempRoadLayer = [...roadLayer];
    
    // 清空次级道路，只保留主干道
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // 如果不是主干道位置，暂时清除
        if (roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY && 
            !horizontalMajorRoads.includes(y) && 
            !verticalMajorRoads.includes(x)) {
          tempRoadLayer[y * width + x] = this.TILE_TYPES.EMPTY;
        }
      }
    }
    
    // 标记所有的十字路口位置（主干道交叉点）
    const intersections = [];
    for (const hRoad of horizontalMajorRoads) {
      for (const vRoad of verticalMajorRoads) {
        intersections.push({x: vRoad, y: hRoad});
      }
    }
    
    // 遍历原始道路层，检查每个可能的次级道路
    for (let y = 0; y < height; y++) {
      // 跳过主干道
      if (horizontalMajorRoads.includes(y)) continue;
      
      // 查找这一行的连续道路段
      let roadStart = -1;
      for (let x = 0; x < width; x++) {
        const currentIsRoad = roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY;
        
        // 如果是主干道位置，跳过
        if (verticalMajorRoads.includes(x)) {
          if (roadStart !== -1) {
            // 检查这段道路是否连接了两个十字路口或主干道
            const isConnected = this.checkRoadConnection(roadStart, x-1, y, true, intersections, verticalMajorRoads);
            if (isConnected) {
              // 如果连接了，恢复这段道路
              for (let i = roadStart; i < x; i++) {
                tempRoadLayer[y * width + i] = roadLayer[y * width + i];
              }
            }
            roadStart = -1;
          }
          continue;
        }
        
        // 找到道路段的开始
        if (currentIsRoad && roadStart === -1) {
          roadStart = x;
        }
        // 找到道路段的结束
        else if (!currentIsRoad && roadStart !== -1) {
          // 检查这段道路是否连接了两个十字路口或主干道
          const isConnected = this.checkRoadConnection(roadStart, x-1, y, true, intersections, verticalMajorRoads);
          if (isConnected) {
            // 如果连接了，恢复这段道路
            for (let i = roadStart; i < x; i++) {
              tempRoadLayer[y * width + i] = roadLayer[y * width + i];
            }
          }
          roadStart = -1;
        }
      }
      
      // 处理延伸到地图边缘的道路
      if (roadStart !== -1) {
        const isConnected = this.checkRoadConnection(roadStart, width-1, y, true, intersections, verticalMajorRoads);
        if (isConnected) {
          for (let i = roadStart; i < width; i++) {
            tempRoadLayer[y * width + i] = roadLayer[y * width + i];
          }
        }
      }
    }
    
    // 同样处理垂直方向的次级道路
    for (let x = 0; x < width; x++) {
      // 跳过主干道
      if (verticalMajorRoads.includes(x)) continue;
      
      // 查找这一列的连续道路段
      let roadStart = -1;
      for (let y = 0; y < height; y++) {
        const currentIsRoad = roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY;
        
        // 如果是主干道位置，跳过
        if (horizontalMajorRoads.includes(y)) {
          if (roadStart !== -1) {
            // 检查这段道路是否连接了两个十字路口或主干道
            const isConnected = this.checkRoadConnection(roadStart, y-1, x, false, intersections, horizontalMajorRoads);
            if (isConnected) {
              // 如果连接了，恢复这段道路
              for (let i = roadStart; i < y; i++) {
                tempRoadLayer[i * width + x] = roadLayer[i * width + x];
              }
            }
            roadStart = -1;
          }
          continue;
        }
        
        // 找到道路段的开始
        if (currentIsRoad && roadStart === -1) {
          roadStart = y;
        }
        // 找到道路段的结束
        else if (!currentIsRoad && roadStart !== -1) {
          // 检查这段道路是否连接了两个十字路口或主干道
          const isConnected = this.checkRoadConnection(roadStart, y-1, x, false, intersections, horizontalMajorRoads);
          if (isConnected) {
            // 如果连接了，恢复这段道路
            for (let i = roadStart; i < y; i++) {
              tempRoadLayer[i * width + x] = roadLayer[i * width + x];
            }
          }
          roadStart = -1;
        }
      }
      
      // 处理延伸到地图边缘的道路
      if (roadStart !== -1) {
        const isConnected = this.checkRoadConnection(roadStart, height-1, x, false, intersections, horizontalMajorRoads);
        if (isConnected) {
          for (let i = roadStart; i < height; i++) {
            tempRoadLayer[i * width + x] = roadLayer[i * width + x];
          }
        }
      }
    }
    
    // 将处理后的道路层复制回原始道路层
    for (let i = 0; i < roadLayer.length; i++) {
      roadLayer[i] = tempRoadLayer[i];
    }
  }
  
  /**
   * 检查道路是否连接了两个十字路口或主干道
   * @param {number} start 道路段起始位置
   * @param {number} end 道路段结束位置
   * @param {number} fixed 固定的行或列
   * @param {boolean} isHorizontal 是否是水平方向的道路
   * @param {Array} intersections 十字路口位置数组
   * @param {Array} majorRoads 主干道位置数组
   * @returns {boolean} 是否连接了两个十字路口或主干道
   */
  checkRoadConnection(start, end, fixed, isHorizontal, intersections, majorRoads) {
    // 检查道路的两端是否都连接到十字路口或主干道
    let startConnected = false;
    let endConnected = false;
    
    if (isHorizontal) {
      // 水平道路
      // 检查左端
      startConnected = start === 0 || majorRoads.includes(start - 1) || 
                      intersections.some(i => i.x === start - 1 && i.y === fixed);
      
      // 检查右端
      endConnected = end === majorRoads.length - 1 || majorRoads.includes(end + 1) || 
                    intersections.some(i => i.x === end + 1 && i.y === fixed);
    } else {
      // 垂直道路
      // 检查上端
      startConnected = start === 0 || majorRoads.includes(start - 1) || 
                      intersections.some(i => i.y === start - 1 && i.x === fixed);
      
      // 检查下端
      endConnected = end === majorRoads.length - 1 || majorRoads.includes(end + 1) || 
                    intersections.some(i => i.y === end + 1 && i.x === fixed);
    }
    
    return startConnected && endConnected;
  }

  /**
   * 移除间隔小于4格的并行道路
   * @param {Array} roadLayer 道路层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  removeCloseParallelRoads(roadLayer, width, height) {
    // 标记要移除的道路位置
    const roadPositionsToRemove = [];

    // 检查水平方向上并行的道路
    for (let y = 1; y < height - 1; y++) {
      for (let x = 0; x < width; x++) {
        // 如果当前位置是道路
        if (roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY) {
          // 检查上下是否有其他道路，并且间隔小于4格
          for (let offset = 1; offset < 4; offset++) { // 原来是3
            // 检查上方
            if (y - offset >= 0) {
              const upIdx = (y - offset) * width + x;
              if (roadLayer[upIdx] !== this.TILE_TYPES.EMPTY) {
                // 如果两条道路之间没有交叉点，标记下方的道路要移除
                let hasIntersection = false;
                for (let checkX = 0; checkX < width; checkX++) {
                  if (roadLayer[y * width + checkX] !== this.TILE_TYPES.EMPTY &&
                    roadLayer[(y - offset) * width + checkX] !== this.TILE_TYPES.EMPTY) {
                    // 有一个交叉点
                    hasIntersection = true;
                    break;
                  }
                }
                if (!hasIntersection) {
                  roadPositionsToRemove.push({ x, y });
                }
              }
            }

            // 检查下方
            if (y + offset < height) {
              const downIdx = (y + offset) * width + x;
              if (roadLayer[downIdx] !== this.TILE_TYPES.EMPTY) {
                // 如果两条道路之间没有交叉点，标记上方的道路要移除
                let hasIntersection = false;
                for (let checkX = 0; checkX < width; checkX++) {
                  if (roadLayer[y * width + checkX] !== this.TILE_TYPES.EMPTY &&
                    roadLayer[(y + offset) * width + checkX] !== this.TILE_TYPES.EMPTY) {
                    // 有一个交叉点
                    hasIntersection = true;
                    break;
                  }
                }
                if (!hasIntersection) {
                  roadPositionsToRemove.push({ x, y });
                }
              }
            }
          }
        }
      }
    }

    // 移除标记的道路位置
    for (const pos of roadPositionsToRemove) {
      roadLayer[pos.y * width + pos.x] = this.TILE_TYPES.EMPTY;
    }
  }

  /**
   * 识别道路类型并更新道路图层
   * @param {Array} roadLayer 道路层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  identifyRoadTypes(roadLayer, width, height) {
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (roadLayer[y * width + x] === this.TILE_TYPES.ROAD) {
          // 检查周围的道路模式
          const hasTop = y > 0 && roadLayer[(y - 1) * width + x] !== this.TILE_TYPES.EMPTY;
          const hasRight = x < width - 1 && roadLayer[y * width + (x + 1)] !== this.TILE_TYPES.EMPTY;
          const hasBottom = y < height - 1 && roadLayer[(y + 1) * width + x] !== this.TILE_TYPES.EMPTY;
          const hasLeft = x > 0 && roadLayer[y * width + (x - 1)] !== this.TILE_TYPES.EMPTY;

          const connectionCount = (hasTop ? 1 : 0) + (hasRight ? 1 : 0) + (hasBottom ? 1 : 0) + (hasLeft ? 1 : 0);

          // 根据连接数量和方向确定道路类型
          if (connectionCount >= 3) {
            // 三向或四向连接都使用十字路口
            roadLayer[y * width + x] = this.TILE_TYPES.ROAD_CROSSROAD;
          } else {
            // 道路末端，使用直线
            if (hasTop || hasBottom) roadLayer[y * width + x] = this.TILE_TYPES.ROAD_VERTICAL;
            else roadLayer[y * width + x] = this.TILE_TYPES.ROAD_HORIZONTAL;
          }
          // 孤立的道路块保持原样
        }
      }
    }
  }

  /**
   * 判断点是否为道路
   * @param {Array} roadLayer 道路层数据
   * @param {number} x 坐标x
   * @param {number} y 坐标y
   * @param {number} width 地图宽度
   * @returns {boolean} 是否为道路
   */
  isRoad(roadLayer, x, y, width) {
    return roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY;
  }

  /**
   * 判断建筑物是否至少有一边与道路相邻
   * @param {Array} roadLayer 道路层数据
   * @param {number} startX 建筑物起始坐标x
   * @param {number} startY 建筑物起始坐标y
   * @param {number} buildingWidth 建筑物宽度
   * @param {number} buildingHeight 建筑物高度
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @returns {boolean} 是否至少有一边与道路相邻
   */
  hasAdjacentRoad(roadLayer, startX, startY, buildingWidth, buildingHeight, width, height) {
    // 检查建筑物的四条边是否有道路相邻

    // 上边缘
    for (let x = startX; x < startX + buildingWidth; x++) {
      if (startY > 0 && this.isRoad(roadLayer, x, startY - 1, width)) {
        return true;
      }
    }

    // 右边缘
    for (let y = startY; y < startY + buildingHeight; y++) {
      if (startX + buildingWidth < width && this.isRoad(roadLayer, startX + buildingWidth, y, width)) {
        return true;
      }
    }

    // 下边缘
    for (let x = startX; x < startX + buildingWidth; x++) {
      if (startY + buildingHeight < height && this.isRoad(roadLayer, x, startY + buildingHeight, width)) {
        return true;
      }
    }

    // 左边缘
    for (let y = startY; y < startY + buildingHeight; y++) {
      if (startX > 0 && this.isRoad(roadLayer, startX - 1, y, width)) {
        return true;
      }
    }

    return false;
  }

  /**
   * 在道路两侧生成建筑物
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} buildings 建筑数据数组
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @returns {Object} 包含zoneLayer的对象
   */
  generateBuildings(sceneLayer, roadLayer, buildings, width, height) {
    // 收集所有道路位置
    const roadPositions = [];

    // 计算地图中心点
    const centerX = Math.floor(width / 2);
    const centerY = Math.floor(height / 2);

    // 计算从中心到最远角落的距离（用于确定环的边界）
    const maxDistance = Math.sqrt(Math.pow(Math.max(centerX, width - centerX), 2) +
      Math.pow(Math.max(centerY, height - centerY), 2));

    // 标记环区
    const zoneLayer = new Array(width * height).fill(this.TILE_TYPES.EMPTY_5); // 默认为边缘区域

    // 设置各环的边界（占总距离的百分比）- 扩大1环，缩小4、5环
    const zone1Radius = maxDistance * 0.15; // 内环占25%（原来是12%）
    const zone2Radius = maxDistance * 0.25; // 内环+二环占45%（原来是36%）
    const zone3Radius = maxDistance * 0.35; // 内环+二环+三环占65%（原来是60%）
    const zone4Radius = maxDistance * 0.65; // 内环+二环+三环+四环占85%（原来是80%）
    // 四环与边缘区域合并，占比35%（原来是40%）

    // 固定边缘区域为6格
    const edgeWidth = 6;

    // 标记每个位置所属的环区
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // 先检查是否在边缘区域内（上下左右各12格）
        if (x < edgeWidth || y < edgeWidth || x >= width - edgeWidth || y >= height - edgeWidth) {
          zoneLayer[y * width + x] = this.TILE_TYPES.EMPTY_5;
          continue; // 如果是边缘区域，直接跳过后续判断
        }

        // 不在边缘区域的位置，根据到中心的距离设置环区
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
        if (distance <= zone1Radius) {
          zoneLayer[y * width + x] = this.TILE_TYPES.EMPTY_1;
        } else if (distance <= zone2Radius) {
          zoneLayer[y * width + x] = this.TILE_TYPES.EMPTY_2;
        } else if (distance <= zone3Radius) {
          zoneLayer[y * width + x] = this.TILE_TYPES.EMPTY_3;
        } else if (distance <= zone4Radius) {
          zoneLayer[y * width + x] = this.TILE_TYPES.EMPTY_4;
        } else {
          // 在4环外但不在边缘区域内的区域也标记为5环(边缘风格区域)
          zoneLayer[y * width + x] = this.TILE_TYPES.EMPTY_5;
        }
      }
    }
    // 收集道路位置
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY) {
          roadPositions.push({ x, y });
        }
      }
    }
    // 按环区优先级放置楼房建筑
    this.placeBuildingsByZone(sceneLayer, roadLayer, zoneLayer, roadPositions, buildings, width, height);

    // 在剩余空地上尝试放置别墅建筑
    this.fillEmptyAreasWithBuildings(sceneLayer, roadLayer, zoneLayer, buildings, width, height);

    return { zoneLayer };
  }

  /**
   * 按环区优先级放置楼房建筑
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} zoneLayer 环区层数据
   * @param {Array} roadPositions 道路位置数组
   * @param {Array} buildings 建筑数据数组
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  placeBuildingsByZone(sceneLayer, roadLayer, zoneLayer, roadPositions, buildings, width, height) {
    // 按环区优先级定义建筑物类型顺序（从大到小）
    const zoneBuildingTypes = {
      [this.TILE_TYPES.EMPTY_1]: [
        this.TILE_TYPES.BUILDING_4X4,       // 4x4
        this.TILE_TYPES.BUILDING_EXTRA_LARGE, // 3x3
      ],
      [this.TILE_TYPES.EMPTY_2]: [
        this.TILE_TYPES.BUILDING_EXTRA_LARGE, // 3x3
        this.TILE_TYPES.BUILDING_2X3,       // 2x3
      ],
      [this.TILE_TYPES.EMPTY_3]: [
        this.TILE_TYPES.BUILDING_3X4,       // 3x4
        this.TILE_TYPES.BUILDING_2X3,       // 2x3
        this.TILE_TYPES.BUILDING_LARGE,     // 2x2
        this.TILE_TYPES.BUILDING_MEDIUM     // 2x1
      ],
      [this.TILE_TYPES.EMPTY_4]: [],
      // 边缘区域不放置任何建筑
      [this.TILE_TYPES.EMPTY_5]: []
    };

    // 按环区优先级处理（从内到外）
    const zoneOrder = [
      this.TILE_TYPES.EMPTY_1,
      this.TILE_TYPES.EMPTY_2,
      this.TILE_TYPES.EMPTY_3,
      this.TILE_TYPES.EMPTY_4
    ];

    // 遍历每个环区
    for (const currentZone of zoneOrder) {
      // 获取当前环区的建筑类型优先级
      const buildingTypesByPriority = zoneBuildingTypes[currentZone];

      // 提取当前环区的数字（1-5）
      const zoneNumber = this.extractZoneNumber(currentZone);

      // 遍历每种建筑类型（按优先级从高到低）
      for (const buildingType of buildingTypesByPriority) {
        // 遍历每个道路位置
        for (const road of roadPositions) {
          // 检查道路的四个方向
          const directions = [
            { dx: -1, dy: 0 }, // 左
            { dx: 1, dy: 0 },  // 右
            { dx: 0, dy: -1 }, // 上
            { dx: 0, dy: 1 }   // 下
          ];

          for (const dir of directions) {
            const buildingX = road.x + dir.dx;
            const buildingY = road.y + dir.dy;

            // 确保位置在地图边界内
            if (buildingX < 0 || buildingX >= width || buildingY < 0 || buildingY >= height) {
              continue;
            }

            // 获取当前位置的环区
            const positionZone = zoneLayer[buildingY * width + buildingX];

            // 只在当前处理的环区内放置建筑
            if (positionZone !== currentZone) {
              continue;
            }

            // 根据建筑类型决定尺寸
            const dimensions = this.getBuildingDimensions(buildingType);
            const buildingWidth = dimensions.width;
            const buildingHeight = dimensions.height;

            // 检查是否能放置建筑（不与道路重叠，不超出地图边界，不与其他建筑重叠）
            let canPlace = true;

            // 检查是否超出地图边界
            if (buildingX + buildingWidth > width || buildingY + buildingHeight > height) {
              canPlace = false;
            }

            // 检查建筑是否会延伸到其他环区
            if (canPlace) {
              for (let y = 0; y < buildingHeight; y++) {
                for (let x = 0; x < buildingWidth; x++) {
                  const checkX = buildingX + x;
                  const checkY = buildingY + y;
                  if (zoneLayer[checkY * width + checkX] !== currentZone) {
                    canPlace = false;
                    break;
                  }
                }
                if (!canPlace) break;
              }
            }

            // 检查是否与道路或其他建筑重叠
            if (canPlace) {
              for (let y = 0; y < buildingHeight; y++) {
                for (let x = 0; x < buildingWidth; x++) {
                  const checkX = buildingX + x;
                  const checkY = buildingY + y;

                  // 检查是否与道路重叠
                  if (roadLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY) {
                    canPlace = false;
                    break;
                  }

                  // 检查是否与其他建筑重叠
                  if (sceneLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY) {
                    canPlace = false;
                    break;
                  }
                }
                if (!canPlace) break;
              }
            }

            // 检查是否至少有一边与道路相邻
            if (canPlace) {
              canPlace = this.hasAdjacentRoad(roadLayer, buildingX, buildingY, buildingWidth, buildingHeight, width, height);
            }

            // 如果可以放置，则放置建筑物
            if (canPlace) {
              // 获取建筑配置
              const config = this.BUILDING_TYPE_CONFIG[buildingType];
              // console.log('buildingType', buildingType, config);
              // 添加建筑数据
              buildings.push({
                type: buildingType,
                x: buildingX,
                y: buildingY,
                width: buildingWidth,
                height: buildingHeight,
                zone: zoneNumber, // 使用提取的环区数字
                floors: config.defaultFloors,
                maxFloors: config.maxFloors,
                style: config.style,
                capacity: config.defaultFloors * this.getUnitCapacity() * config.width * this.Probability
              });

              // 放置建筑
              for (let y = 0; y < buildingHeight; y++) {
                for (let x = 0; x < buildingWidth; x++) {
                  const placeX = buildingX + x;
                  const placeY = buildingY + y;
                  sceneLayer[placeY * width + placeX] = buildingType;
                }
              }
            }
          }
        }
      }
    }
  }

  /**
   * 在剩余空地上尝试放置别墅建筑
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} zoneLayer 环区层数据
   * @param {Array} buildings 建筑数据数组
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  fillEmptyAreasWithBuildings(sceneLayer, roadLayer, zoneLayer, buildings, width, height) {
    // 收集所有道路位置
    const roadPositions = [];
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (roadLayer[y * width + x] !== this.TILE_TYPES.EMPTY) {
          roadPositions.push({ x, y });
        }
      }
    }

    // 别墅类型优先级（从大到小）
    const villaTypes = [
      this.TILE_TYPES.VILLA_3X3,  // 3x3别墅
      this.TILE_TYPES.VILLA_3X2,  // 3x2别墅
      this.TILE_TYPES.VILLA_2X3,  // 2x3别墅
      this.TILE_TYPES.VILLA_2X2   // 2x2别墅
    ];

    // 遍历每个道路位置
    for (const road of roadPositions) {
      // 检查道路的四个方向
      const directions = [
        { dx: -1, dy: 0 }, // 左
        { dx: 1, dy: 0 },  // 右
        { dx: 0, dy: -1 }, // 上
        { dx: 0, dy: 1 }   // 下
      ];

      for (const dir of directions) {
        // 遍历每种别墅类型
        for (const villaType of villaTypes) {
          const startX = road.x + dir.dx;
          const startY = road.y + dir.dy;

          // 确保位置在地图边界内
          if (startX < 0 || startX >= width || startY < 0 || startY >= height) {
            continue;
          }

          // // 获取当前位置的环区
          // const currentZone = zoneLayer[startY * width + startX];

          // // 提取环区数字（1-5）
          // const zoneNumber = this.extractZoneNumber(currentZone);

          // // 跳过一环和二环，只在三环、四环及边缘区域放置别墅
          // if (currentZone === this.TILE_TYPES.EMPTY_1 || currentZone === this.TILE_TYPES.EMPTY_2) {
          //   continue;
          // }

          // 获取别墅尺寸
          const dimensions = this.getBuildingDimensions(villaType);
          const villaWidth = dimensions.width;
          const villaHeight = dimensions.height;

          // 检查是否能放置别墅
          let canPlace = true;

          // 检查是否超出地图边界
          if (startX + villaWidth > width || startY + villaHeight > height) {
            canPlace = false;
          }

          // // 检查建筑是否会延伸到一环或二环
          // if (canPlace) {
          //   for (let y = 0; y < villaHeight; y++) {
          //     for (let x = 0; x < villaWidth; x++) {
          //       const checkX = startX + x;
          //       const checkY = startY + y;
          //       const checkZone = zoneLayer[checkY * width + checkX];
          //       if (checkZone === this.TILE_TYPES.EMPTY_1 ||
          //         checkZone === this.TILE_TYPES.EMPTY_2 ||
          //         checkZone === this.TILE_TYPES.EMPTY_5) {
          //         canPlace = false;
          //         break;
          //       }
          //     }
          //     if (!canPlace) break;
          //   }
          // }

          // 检查是否与道路或其他建筑重叠
          if (canPlace) {
            for (let y = 0; y < villaHeight; y++) {
              for (let x = 0; x < villaWidth; x++) {
                const checkX = startX + x;
                const checkY = startY + y;

                // 确保不超出地图边界
                if (checkX >= width || checkY >= height) {
                  canPlace = false;
                  break;
                }

                // 检查该位置是否已有建筑或道路
                if (sceneLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY ||
                  roadLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY) {
                  canPlace = false;
                  break;
                }
              }
              if (!canPlace) break;
            }
          }

          // 检查是否至少有一边与道路相邻
          if (canPlace) {
            canPlace = this.hasAdjacentRoad(roadLayer, startX, startY, villaWidth, villaHeight, width, height);
          }

          // 如果可以放置，放置别墅
          if (canPlace) {
            // 获取别墅配置
            const config = this.BUILDING_TYPE_CONFIG[villaType];

            // 添加别墅数据
            buildings.push({
              type: villaType,
              x: startX,
              y: startY,
              width: villaWidth,
              height: villaHeight,
              // zone: zoneNumber, // 使用提取的环区数字
              floors: config.defaultFloors,
              maxFloors: config.maxFloors,
              style: config.style,
              capacity: 0
            });

            // 放置别墅
            for (let y = 0; y < villaHeight; y++) {
              for (let x = 0; x < villaWidth; x++) {
                const placeX = startX + x;
                const placeY = startY + y;
                sceneLayer[placeY * width + placeX] = villaType;
              }
            }
            // 成功放置后跳出别墅类型循环，继续检查下一个方向
            break;
          }
        }
      }
    }

    // 第二次填充：扫描整个地图寻找可放置别墅的空地
    this.fillRemainingSpacesWithVillas(sceneLayer, roadLayer, zoneLayer, buildings, width, height);
  }

  /**
   * 在剩余的空地上寻找可放置别墅的位置
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} zoneLayer 环区层数据
   * @param {Array} buildings 建筑数据数组
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   */
  fillRemainingSpacesWithVillas(sceneLayer, roadLayer, zoneLayer, buildings, width, height) {
    // 别墅类型优先级（从大到小）
    const villaTypes = [
      this.TILE_TYPES.VILLA_3X3,  // 3x3别墅
      this.TILE_TYPES.VILLA_3X2,  // 3x2别墅
      this.TILE_TYPES.VILLA_2X3,  // 2x3别墅
      this.TILE_TYPES.VILLA_2X2   // 2x2别墅
    ];

    // 划分地图为区块，每个区块尝试放置一个别墅
    const blockSize = 3; // 每3x3格尝试放置一个别墅

    for (let blockY = 0; blockY < height; blockY += blockSize) {
      for (let blockX = 0; blockX < width; blockX += blockSize) {
        // 选择区块内的起点
        const startX = blockX;
        const startY = blockY;

        // 如果起点超出地图范围，跳过
        if (startX >= width || startY >= height) continue;

        // 如果起点已经有建筑或道路，跳过
        if (sceneLayer[startY * width + startX] !== this.TILE_TYPES.EMPTY ||
          roadLayer[startY * width + startX] !== this.TILE_TYPES.EMPTY) {
          continue;
        }

        // 获取当前位置的环区
        const currentZone = zoneLayer[startY * width + startX];

        // 提取环区数字（1-5）
        const zoneNumber = this.extractZoneNumber(currentZone);

        // 跳过一环、二环和边缘区域(zone=5)，只在三环和四环放置别墅
        if (currentZone === this.TILE_TYPES.EMPTY_1 ||
          currentZone === this.TILE_TYPES.EMPTY_2 ||
          currentZone === this.TILE_TYPES.EMPTY_5) {
          continue;
        }

        // 尝试每种别墅类型
        for (const villaType of villaTypes) {
          // 获取别墅尺寸
          const dimensions = this.getBuildingDimensions(villaType);
          const villaWidth = dimensions.width;
          const villaHeight = dimensions.height;

          // 检查是否能放置别墅
          let canPlace = true;

          // 检查是否超出地图边界
          if (startX + villaWidth > width || startY + villaHeight > height) {
            canPlace = false;
          }

          // 检查建筑是否会延伸到一环或二环
          if (canPlace) {
            for (let y = 0; y < villaHeight; y++) {
              for (let x = 0; x < villaWidth; x++) {
                const checkX = startX + x;
                const checkY = startY + y;
                const checkZone = zoneLayer[checkY * width + checkX];
                if (checkZone === this.TILE_TYPES.EMPTY_1 ||
                  checkZone === this.TILE_TYPES.EMPTY_2 ||
                  checkZone === this.TILE_TYPES.EMPTY_5) {
                  canPlace = false;
                  break;
                }
              }
              if (!canPlace) break;
            }
          }

          // 检查是否与道路或其他建筑重叠
          if (canPlace) {
            for (let y = 0; y < villaHeight; y++) {
              for (let x = 0; x < villaWidth; x++) {
                const checkX = startX + x;
                const checkY = startY + y;

                // 确保不超出地图边界
                if (checkX >= width || checkY >= height) {
                  canPlace = false;
                  break;
                }

                // 检查该位置是否已有建筑或道路
                if (sceneLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY ||
                  roadLayer[checkY * width + checkX] !== this.TILE_TYPES.EMPTY) {
                  canPlace = false;
                  break;
                }
              }
              if (!canPlace) break;
            }
          }

          // 检查是否至少有一边与道路相邻
          if (canPlace) {
            canPlace = this.hasAdjacentRoad(roadLayer, startX, startY, villaWidth, villaHeight, width, height);
          }

          // 如果可以放置，放置别墅
          if (canPlace) {
            // 获取别墅配置
            const config = this.BUILDING_TYPE_CONFIG[villaType];

            // 添加别墅数据
            buildings.push({
              type: villaType,
              x: startX,
              y: startY,
              width: villaWidth,
              height: villaHeight,
              zone: zoneNumber, // 使用提取的环区数字
              floors: config.defaultFloors,
              maxFloors: config.maxFloors,
              style: config.style,
              capacity: 0
            });

            // 放置别墅
            for (let y = 0; y < villaHeight; y++) {
              for (let x = 0; x < villaWidth; x++) {
                const placeX = startX + x;
                const placeY = startY + y;
                sceneLayer[placeY * width + placeX] = villaType;
              }
            }
            // 成功放置后跳出别墅类型循环
            break;
          }
        }
      }
    }
  }

  /**
   * 检查一个区域是否为空地
   * @param {Array} roadLayer 道路图层数据
   * @param {Array} sceneLayer 建筑图层数据
   * @param {Array} decorationLayer 装饰图层数据
   * @param {number} startX 起始X坐标
   * @param {number} startY 起始Y坐标
   * @param {number} width 区域宽度
   * @param {number} height 区域高度
   * @param {number} mapWidth 地图宽度
   * @returns {boolean} 是否为空地
   */
  isEmptyArea(roadLayer, sceneLayer, decorationLayer, startX, startY, width, height, mapWidth) {
    // 检查区域是否超出地图边界
    if (startX < 0 || startY < 0 || startX + width > mapWidth) {
      return false;
    }

    // 检查区域内的每个格子是否都为空
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const checkX = startX + x;
        const checkY = startY + y;
        const index = checkY * mapWidth + checkX;

        // 检查该位置是否有道路、建筑或装饰
        if (roadLayer[index] !== this.TILE_TYPES.EMPTY ||
          sceneLayer[index] !== this.TILE_TYPES.EMPTY ||
          decorationLayer[index] !== this.TILE_TYPES.EMPTY) {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * 统计地图中各种瓦片的数量
   * @param {Array} groundLayer 地面层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} decorationLayer 装饰层数据
   * @returns {Object} 各类瓦片的数量统计
   */
  countTiles(groundLayer, roadLayer, sceneLayer, decorationLayer) {
    const counts = {
      ground: {},
      roads: {},
      buildings: {},
      decorations: {}
    };

    // 统计地面层
    for (const tileId of groundLayer) {
      counts.ground[tileId] = (counts.ground[tileId] || 0) + 1;
    }

    // 统计道路层
    for (const tileId of roadLayer) {
      counts.roads[tileId] = (counts.roads[tileId] || 0) + 1;
    }

    // 统计建筑层
    for (const tileId of sceneLayer) {
      counts.buildings[tileId] = (counts.buildings[tileId] || 0) + 1;
    }

    // 统计装饰层
    for (const tileId of decorationLayer) {
      counts.decorations[tileId] = (counts.decorations[tileId] || 0) + 1;
    }

    return counts;
  }

  /**
   * 判断是否是建筑的左上角起始点
   * @param {Array} sceneLayer 建筑层数据
   * @param {number} x X坐标
   * @param {number} y Y坐标
   * @param {number} width 地图宽度
   * @param {number} buildingType 建筑类型
   * @returns {boolean} 是否是建筑的起始点
   */
  isStartingBuildingTile(sceneLayer, x, y, width, buildingType) {
    // 获取建筑尺寸
    const dimensions = this.getBuildingDimensions(buildingType);
    let buildingWidth = dimensions.width;
    let buildingHeight = dimensions.height;

    // 检查左上位置是否真的是起始点
    // 如果左边和上边都没有相同类型的建筑，则认为是起始点
    const leftTile = x > 0 ? sceneLayer[y * width + (x - 1)] : this.TILE_TYPES.EMPTY;
    const upTile = y > 0 ? sceneLayer[(y - 1) * width + x] : this.TILE_TYPES.EMPTY;

    return leftTile !== buildingType && upTile !== buildingType;
  }

  /**
   * 根据人口调整建筑高度
   * @param {Array} buildings 建筑数据数组
   * @param {number} population 城市人口总数
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @returns {Object} 包含调整结果的对象
   */
  adjustBuildingHeights(buildings, population, width, height) {
    // 计算初始人口容量
    let totalCapacity = Math.floor((width - 12) * (height - 12) / 10);
    console.log(`调整建筑高度以适应人口: ${population}`, width, height, totalCapacity);
    for (const building of buildings) {
      // 跳过边缘区域的建筑（应该没有，以防万一）
      if (building.zone === 5) continue;
      totalCapacity += building.capacity;
    }

    console.log(`初始人口容量: ${totalCapacity}`);

    // 如果初始容量已经足够，不需要调整
    if (totalCapacity >= population) {
      console.log(`初始容量足够，无需调整建筑高度`);
      return { needEnlarge: false };
    }

    console.log(`需要增加容量: ${population - totalCapacity}`);

    // 按照环区优先级循环遍历建筑
    let priorityCycle = [
      { zone: 1, times: 3 },
      { zone: 2, times: 2 },
      { zone: 3, times: 2 },
      { zone: 4, times: 1 }
    ];
    // 边缘区域(zone=5)不参与调整

    while (totalCapacity < population) {
      let madeChanges = false;

      // 按优先级遍历环区
      for (const priority of priorityCycle) {
        // 每个环区遍历指定次数
        for (let i = 0; i < priority.times; i++) {
          let addedFloorInThisCycle = false;

          // 遍历当前环区的所有建筑
          for (const building of buildings) {
            if (building.zone === priority.zone) {
              // 使用建筑自身的maxFloors限制
              const maxFloors = building.maxFloors;

              // 如果还可以增加层数
              if (building.floors < maxFloors) {
                // 增加一层
                building.floors++;

                // 增加容量 - 确保与初始化一致，都是每层10人*宽度
                const capacityPerFloor = this.getUnitCapacity() * building.width * this.Probability;
                totalCapacity += capacityPerFloor;
                building.capacity += capacityPerFloor;
                // console.log(`增加一层到建筑 (${building.x}, ${building.y})，现在是 ${building.floors} 层，新增容量 ${capacityPerFloor}，总容量 ${totalCapacity}`);

                madeChanges = true;

                // 如果容量已达到要求，退出
                if (totalCapacity >= population) {
                  return { needEnlarge: false };
                }
              }
            }
          }

          // 如果这一轮没有任何建筑可以增加层数，跳出内层循环
          if (!madeChanges) {
            break;
          }
        }
      }

      // 如果一轮遍历后没有任何建筑可以增加层数
      if (!madeChanges) {
        // 所有建筑都达到最大层数，需要增大地图尺寸
        console.log(`所有建筑都达到最大层数，需要增大地图尺寸并重新生成`);
        return { needEnlarge: true };
      }
    }

    console.log(`调整后的总人口容量: ${totalCapacity}`);
    return { needEnlarge: false };
  }

  /**
   * 获取建筑尺寸
   * @param {number} buildingType 建筑类型ID
   * @returns {Object} 包含width和height属性的对象
   */
  getBuildingDimensions(buildingType) {
    if (this.BUILDING_TYPE_CONFIG[buildingType]) {
      return {
        width: this.BUILDING_TYPE_CONFIG[buildingType].width,
        height: this.BUILDING_TYPE_CONFIG[buildingType].height
      };
    }
    // 默认返回1x1尺寸
    return { width: 1, height: 1 };
  }

  /**
   * 从环区类型中提取数字（1-5）
   * @param {number} zoneType 环区类型
   * @returns {number} 环区数字（1-5）
   */
  extractZoneNumber(zoneType) {
    // 环区类型对应的数字映射
    switch (zoneType) {
      case this.TILE_TYPES.EMPTY_1:
        return 1;
      case this.TILE_TYPES.EMPTY_2:
        return 2;
      case this.TILE_TYPES.EMPTY_3:
        return 3;
      case this.TILE_TYPES.EMPTY_4:
        return 4;
      case this.TILE_TYPES.EMPTY_5:
        return 5;
      default:
        return 5; // 默认为边缘区域
    }
  }

  /**
   * 获取单位容量值
   * @returns {number} 单位容量值，默认为5
   */
  getUnitCapacity() {
    try {
      // 尝试获取gameStore
      if (!this.gameStore) {
        this.gameStore = useGameStore();
      }
      return this.gameStore.unitCapacity;
    } catch (error) {
      console.warn('获取unitCapacity失败，使用默认值5', error);
      return 5; // 默认值
    }
  }

  /**
   * 放置装饰物
   * @param {Array} decorationLayer 装饰层数据
   * @param {number} startX 起始X坐标
   * @param {number} startY 起始Y坐标
   * @param {number} decorationType 装饰类型
   * @param {number} width 宽度
   * @param {number} height 高度
   * @param {number} mapWidth 地图宽度
   */
  placeDecoration(decorationLayer, startX, startY, decorationType, width, height, mapWidth) {
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const placeX = startX + x;
        const placeY = startY + y;
        decorationLayer[placeY * mapWidth + placeX] = decorationType;
      }
    }
  }

  /**
   * 生成装饰物
   * @param {Array} decorationLayer 装饰层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} zoneLayer 环区层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @param {Array} groundLayer 地面层数据
   * @returns {Array} 装饰物数据数组
   */
  generateDecorations(decorationLayer, roadLayer, sceneLayer, zoneLayer, width, height, groundLayer) {
    // 存储所有装饰物数据
    const decorations = [];
    
    console.log(`开始生成装饰物，地图尺寸: ${width}x${height}`);
    
    // 设置不同环区的装饰物类型
    const decorationTypesByZone = {
      // 大型装饰物类型 (3x3)
      large: {
        [this.TILE_TYPES.EMPTY_5]: this.TILE_TYPES.FOUNTAIN, // 无人区 - 喷泉
        other: this.TILE_TYPES.PARK                          // 其他环区 - 公园
      },
      // 中型装饰物类型 (2x2)
      medium: {
        [this.TILE_TYPES.EMPTY_5]: this.TILE_TYPES.GARDEN,   // 无人区 - 花园
        other: this.TILE_TYPES.TREE_LARGE                    // 其他环区 - 大树
      },
      // 小型装饰物类型 (1x1)
      small: {
        [this.TILE_TYPES.EMPTY_5]: this.TILE_TYPES.BUSH,     // 无人区 - 灌木
        other: this.TILE_TYPES.TREE                          // 其他环区 - 树
      }
    };
    
    // 1. 首先放置大型装饰物 (3x3)
    console.log('开始放置大型装饰物 (3x3)');
    const largePlaced = this.placeDecorationsBySize(
      decorationLayer, roadLayer, sceneLayer, zoneLayer, 
      width, height, 
      decorationTypesByZone.large, 
      3, 3,  // 尺寸为3x3
      decorations,
      groundLayer  // 传递groundLayer
    );
    
    // 2. 然后放置中型装饰物 (2x2)
    console.log('开始放置中型装饰物 (2x2)');
    const mediumPlaced = this.placeDecorationsBySize(
      decorationLayer, roadLayer, sceneLayer, zoneLayer, 
      width, height,
      decorationTypesByZone.medium, 
      2, 2,  // 尺寸为2x2
      decorations,
      groundLayer  // 传递groundLayer
    );
    
    // 3. 最后放置小型装饰物 (1x1)
    console.log('开始放置小型装饰物 (1x1)');
    const smallPlaced = this.placeDecorationsBySize(
      decorationLayer, roadLayer, sceneLayer, zoneLayer, 
      width, height,
      decorationTypesByZone.small, 
      1, 1,  // 尺寸为1x1
      decorations,
      groundLayer  // 传递groundLayer
    );
    
    console.log(`装饰物放置完成，共放置 ${decorations.length} 个装饰物`);
    console.log(`大型装饰物: ${largePlaced}, 中型装饰物: ${mediumPlaced}, 小型装饰物: ${smallPlaced}`);
    
    return decorations;
  }
  
  /**
   * 根据尺寸放置特定类型的装饰物
   * @param {Array} decorationLayer 装饰层数据
   * @param {Array} roadLayer 道路层数据
   * @param {Array} sceneLayer 建筑层数据
   * @param {Array} zoneLayer 环区层数据
   * @param {number} width 地图宽度
   * @param {number} height 地图高度
   * @param {Object} typesByZone 不同环区对应的装饰物类型
   * @param {number} decorWidth 装饰物宽度
   * @param {number} decorHeight 装饰物高度
   * @param {Array} decorations 装饰物数据数组 (用于收集结果)
   * @param {Array} groundLayer 地面层数据
   * @returns {number} 放置的装饰物数量
   */
  placeDecorationsBySize(decorationLayer, roadLayer, sceneLayer, zoneLayer, width, height, typesByZone, decorWidth, decorHeight, decorations, groundLayer) {
    let placedCount = 0;
    
    // 固定边缘区域宽度为6格
    const edgeWidth = 0;
    
    // 按间隔划分地图遍历
    const stepSize = Math.max(decorWidth, decorHeight);
    
    // 遍历整个地图
    for (let y = edgeWidth; y < height - edgeWidth - decorHeight + 1; y += stepSize) {
      for (let x = edgeWidth; x < width - edgeWidth - decorWidth + 1; x += stepSize) {
        // 获取当前位置的环区
        const currentZone = zoneLayer[y * width + x];
        
        // 确定要放置的装饰物类型 (基于环区)
        let decorationType;
        if (currentZone === this.TILE_TYPES.EMPTY_5) {
          decorationType = typesByZone[this.TILE_TYPES.EMPTY_5];
        } else {
          decorationType = typesByZone.other;
        }
        
        // 检查区域是否为空
        if (this.isEmptyArea(roadLayer, sceneLayer, decorationLayer, x, y, decorWidth, decorHeight, width)) {
          // 如果是草地且要放置的是树，则跳过
          if (groundLayer && 
              groundLayer[y * width + x] === this.TILE_TYPES.GRASS && 
              decorationType === this.TILE_TYPES.TREE) {
            continue;
          }
          
          // 获取装饰物配置
          const config = this.BUILDING_TYPE_CONFIG[decorationType];
          
          // 添加装饰物数据
          decorations.push({
            type: decorationType,
            x: x,
            y: y,
            width: decorWidth,
            height: decorHeight,
            style: config.style,
            decorationType: config.type
          });
          
          // 在地图上放置装饰物
          this.placeDecoration(decorationLayer, x, y, decorationType, decorWidth, decorHeight, width);
          
          // 计数
          placedCount++;
        }
      }
    }
    
    return placedCount;
  }
}

export default MapGenerator; 