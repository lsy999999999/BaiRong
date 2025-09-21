/**
 * TileInteractionHandler.js
 * 处理地图瓦片的交互事件，包括鼠标悬停和点击事件
 */

import { useGameStore } from '../../stores/gameStore';

/**
 * 确定当前位置的环区类型
 * @param {number} tileIndex - 瓦片索引
 * @param {object} mapData - 地图数据
 * @returns {string} 环区名称
 */
export function determineZoneType(tileIndex, mapData) {
  if (!mapData || !mapData.layers) {
    return '未知区域';
  }

  // 从mapData中获取zoneLayer数据
  const zoneLayer = mapData.zoneLayer;
  
  // 如果有zoneLayer数据，直接根据zoneLayer确定环区
  if (zoneLayer && zoneLayer[tileIndex] !== undefined) {
    // 获取当前位置的环区值
    const zoneValue = zoneLayer[tileIndex];
    
    // 根据环区值返回对应的环区名称
    switch (zoneValue) {
      case 100: // TILE_TYPES.EMPTY_1
        return '1环 (核心区)';
      case 101: // TILE_TYPES.EMPTY_2
        return '2环 (中心区)';
      case 102: // TILE_TYPES.EMPTY_3
        return '3环 (外围区)';
      case 103: // TILE_TYPES.EMPTY_4
        return '4环 (别墅区)';
      case 104: // TILE_TYPES.EMPTY_5
        return '5环 (无人区)';
      default:
        return `未知区域 (区域代码: ${zoneValue})`;
    }
  }
  
  // 如果没有zoneLayer数据，使用距离计算方法
  const centerX = Math.floor(mapData.width / 2);
  const centerY = Math.floor(mapData.height / 2);
  const x = tileIndex % mapData.width;
  const y = Math.floor(tileIndex / mapData.width);

  // 计算到中心的距离
  const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));

  // 计算最远距离
  const maxDistance = Math.sqrt(
    Math.pow(Math.max(centerX, mapData.width - centerX), 2) +
    Math.pow(Math.max(centerY, mapData.height - centerY), 2)
  );

  // 计算所在环区
  if (distance <= maxDistance * 0.2) {
    return '1环 (核心区)';
  } else if (distance <= maxDistance * 0.45) {
    return '2环 (中心区)';
  } else if (distance <= maxDistance * 0.7) {
    return '3环 (外围区)';
  } else {
    return '4环 (边缘区)';
  }
}

/**
 * 获取当前位置的建筑信息
 * @param {number} tileIndex - 瓦片索引
 * @param {object} mapData - 地图数据
 * @param {object} buildingRenderer - 建筑渲染器实例
 * @param {object} sceneLayer - 场景图层
 * @returns {object} 建筑信息对象
 */
export function getBuildingInfo(tileIndex, mapData, buildingRenderer, sceneLayer) {
  const result = {
    buildingInfo: '',
    buildingId: '',
    floors: 0,
    width: 0,
    height: 0
  };

  if (!mapData || !mapData.layers) {
    return result;
  }

  // 获取建筑层
  const buildingLayer = mapData.layers.find(layer => layer.name === "Buildings");
  if (!buildingLayer || !buildingLayer.data) {
    return result;
  }

  // 获取当前位置的建筑类型
  const buildingType = buildingLayer.data[tileIndex];

  // 如果没有建筑，返回空信息
  if (!buildingType || buildingType === 0) {
    return result;
  }

  // 获取当前网格坐标
  const x = tileIndex % mapData.width;
  const y = Math.floor(tileIndex / mapData.width);

  // 获取游戏状态store
  const gameStore = useGameStore();
  
  // 尝试从window.gridToBuildingMap获取建筑ID
  const buildingId = gameStore.getBuildingAt(x, y);

  if (buildingId && buildingRenderer) {
    // 获取建筑数据
    const buildingData = buildingRenderer.getBuildingData(buildingId);

    if (buildingData) {
      result.buildingId = buildingId;
      result.floors = buildingData.floors || 0;

      // 查找建筑精灵获取更多信息
      if (sceneLayer) {
        for (let i = 0; i < sceneLayer.children.length; i++) {
          const sprite = sceneLayer.children[i];
          if (sprite.buildingId === buildingId) {
            result.width = sprite.buildingGridWidth || 0;
            result.height = sprite.buildingGridHeight || 0;
            break;
          }
        }
      }
    }
  }

  // 根据建筑类型设置信息
  switch (buildingType) {
    case 21: // BUILDING_MEDIUM
      result.buildingInfo = '中型建筑 (2x1)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 1;
      break;
    case 22: // BUILDING_LARGE
      result.buildingInfo = '大型建筑 (2x2)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 2;
      break;
    case 23: // BUILDING_EXTRA_LARGE
      result.buildingInfo = '特大型建筑 (3x3)';
      if (!result.width) result.width = 3;
      if (!result.height) result.height = 3;
      break;
    case 24: // BUILDING_4X4
      result.buildingInfo = '超大型建筑 (4x4)';
      if (!result.width) result.width = 4;
      if (!result.height) result.height = 4;
      break;
    case 25: // BUILDING_2X3
      result.buildingInfo = '长型建筑 (2x3)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 3;
      break;
    case 26: // BUILDING_3X4
      result.buildingInfo = '工厂建筑 (3x4)';
      if (!result.width) result.width = 3;
      if (!result.height) result.height = 4;
      break;
    case 27: // VILLA_2X2
      result.buildingInfo = '别墅 (2x2)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 2;
      break;
    case 28: // VILLA_3X2
      result.buildingInfo = '别墅 (3x2)';
      if (!result.width) result.width = 3;
      if (!result.height) result.height = 2;
      break;
    case 29: // VILLA_2X3
      result.buildingInfo = '别墅 (2x3)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 3;
      break;
    case 30: // VILLA_3X3
      result.buildingInfo = '别墅 (3x3)';
      if (!result.width) result.width = 3;
      if (!result.height) result.height = 3;
      break;
    case 40: // TREE
      result.buildingInfo = '树 (1x1)';
      if (!result.width) result.width = 1;
      if (!result.height) result.height = 1;
      break;
    case 41: // BUSH
      result.buildingInfo = '灌木 (1x1)';
      if (!result.width) result.width = 1;
      if (!result.height) result.height = 1;
      break;
    case 42: // TREE_LARGE
      result.buildingInfo = '大树 (2x2)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 2;
      break;
    case 43: // GARDEN
      result.buildingInfo = '花园 (2x2)';
      if (!result.width) result.width = 2;
      if (!result.height) result.height = 2;
      break;
    case 44: // PARK
      result.buildingInfo = '公园 (3x3)';
      if (!result.width) result.width = 3;
      if (!result.height) result.height = 3;
      break;
    case 45: // FOUNTAIN
      result.buildingInfo = '喷泉 (3x3)';
      if (!result.width) result.width = 3;
      if (!result.height) result.height = 3;
      break;
    default:
      result.buildingInfo = `未知建筑 (ID: ${buildingType})`;
  }

  // 如果没有楼层信息，生成一个合理的默认值
  if (!result.floors) {
    // 基于建筑高度估算楼层数
    const baseFloors = Math.ceil(Math.max(result.width, result.height) / 2);
    result.floors = Math.max(1, baseFloors);
  }

  return result;
}

/**
 * 处理鼠标悬停事件
 * @param {number} tileIndex - 瓦片索引
 * @param {object} mapData - 地图数据
 * @param {object} buildingRenderer - 建筑渲染器实例
 * @param {object} sceneLayer - 场景图层
 * @returns {object} 包含环区和建筑信息的对象
 */
export function handleTileHover(tileIndex, mapData, buildingRenderer, sceneLayer) {
  const zoneType = determineZoneType(tileIndex, mapData);
  const buildingInfo = getBuildingInfo(tileIndex, mapData, buildingRenderer, sceneLayer);
  
  return {
    zoneType,
    ...buildingInfo
  };
}

/**
 * 处理瓦片点击事件
 * @param {number} tileIndex - 瓦片索引
 * @param {object} mapData - 地图数据
 * @param {object} buildingRenderer - 建筑渲染器实例
 * @param {object} sceneLayer - 场景图层
 * @returns {object} 点击事件处理结果
 */
export function handleTileClick(tileIndex, mapData, buildingRenderer, sceneLayer) {
  const hoverInfo = handleTileHover(tileIndex, mapData, buildingRenderer, sceneLayer);
  
  // 返回点击信息
  return {
    ...hoverInfo,
    x: tileIndex % mapData.width,
    y: Math.floor(tileIndex / mapData.width),
    tileIndex
  };
} 

