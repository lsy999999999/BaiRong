/**
 * 人物行为控制器
 * 负责管理和控制人物的移动行为和AI决策
 */
import * as PIXI from 'pixi.js';
import { useGameStore } from '../../stores/gameStore';

class CharacterBehavior {
  constructor() {
    this.characterPositions = new Map(); // 存储所有人物当前位置，用于避免碰撞
    this.pathCache = new Map();  // 缓存计算过的路径
  }


  /**
   * 设置角色位置信息
   * @param {Map} characterPositions 角色位置映射
   */
  setCharacterPositions(characterPositions) {
    this.characterPositions = characterPositions;
  }

  /**
   * 人物随机移动
   * @param {Object} character 人物数据
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @returns {boolean} 是否成功开始移动
   */
  moveRandomly(character, tileWidth, tileHeight, mapWidth, mapHeight) {
    // 检查角色是否被鼠标悬停暂停
    if (character.isPausedByHover) {
      return false;
    }

    // 重置建筑寻找计时器
    character.roadWalkingTime = 0;
    character.isSearchingBuilding = false;
    character.isGoingToBuilding = false;
    character.targetBuilding = null;

    // 边缘区域宽度（格子数）
    const edgeWidth = 6;

    // 当前所在网格坐标
    const currentGridX = Math.floor(character.x / tileWidth);
    const currentGridY = Math.floor(character.y / tileHeight);

    // 检查角色是否在道路上
    if (!this.isOnRoad(currentGridX, currentGridY)) {
      // console.log(`角色${character.id}不在道路上，寻找最近的道路点`);

      // 寻找最近的道路点
      const nearestRoadPoint = this.findNearestRoadPoint(currentGridX, currentGridY);

      if (nearestRoadPoint) {
        // console.log(`角色${character.id}找到最近的道路点: (${nearestRoadPoint.x}, ${nearestRoadPoint.y})`);

        // 计算从当前位置到最近道路点的路径
        try {
          // 使用A*寻路算法计算路径
          const path = this.findPath(
            currentGridX,
            currentGridY,
            nearestRoadPoint.x,
            nearestRoadPoint.y,
            tileWidth,
            tileHeight
          );

          if (path && path.length > 0) {
            // 设置路径点
            character.pathPoints = path;

            // 设置第一个路径点为目标
            const firstPoint = character.pathPoints.shift();
            character.targetX = firstPoint.x;
            character.targetY = firstPoint.y;
            character.isMoving = true;

            // 更新网格位置
            character.targetGridX = nearestRoadPoint.x;
            character.targetGridY = nearestRoadPoint.y;

            // 更新角色位置映射
            this.characterPositions.delete(`${character.gridX},${character.gridY}`);
            this.characterPositions.set(`${nearestRoadPoint.x},${nearestRoadPoint.y}`, character);

            // console.log(`已设置角色${character.id}移动到最近的道路点`, nearestRoadPoint.x, nearestRoadPoint.y);
            return true;
          }
        } catch (error) {
          console.error(`计算到道路点的路径时出错:`, error);
        }

        // 如果A*寻路失败，尝试使用简单的直线路径
        try {
          // console.log(`尝试使用简单路径移动到道路点`);
          this.setSimpleDetourPath(
            character,
            currentGridX,
            currentGridY,
            nearestRoadPoint.x,
            nearestRoadPoint.y,
            tileWidth,
            tileHeight
          );

          character.isMoving = true;
          return true;
        } catch (error) {
          console.error(`设置简单路径时出错:`, error);
        }
      }
    }

    // 获取角色当前方向
    const currentDirection = character.currentDirection || null;

    // 判断当前位置是否为十字路口
    const isAtIntersection = this.isIntersection(currentGridX, currentGridY);

    // 如果不在十字路口，先移动到最近的十字路口
    if (!isAtIntersection) {
      // 寻找视口内最近的十字路口，不使用全图查找
      const nearestIntersection = this.findNearestIntersection(currentGridX, currentGridY, mapWidth, mapHeight, edgeWidth);

      if (nearestIntersection) {
        // 设置目标为最近的十字路口
        this.moveToIntersection(character, nearestIntersection, tileWidth, tileHeight);
        return true;
      }

      // 如果找不到视口内的十字路口，等待一段时间后重试
      character.moveInterval = 500 + Math.random() * 1000;
      return false;
    }

    // 已经在十字路口，选择下一个方向
    // 获取可用方向（上、右、下、左），传入当前方向用于计算权重
    // 限制搜索范围在视口内
    const availableDirections = this.getAvailableDirectionsInViewport(
      currentGridX,
      currentGridY,
      mapWidth,
      mapHeight,
      edgeWidth,
      currentDirection
    );

    if (availableDirections.length === 0) {
      // 没有可用方向，稍后重试
      character.moveInterval = 500 + Math.random() * 1000;
      return false;
    }

    // 根据权重随机选择一个方向
    // 计算总权重
    const totalWeight = availableDirections.reduce((sum, dir) => sum + dir.weight, 0);

    // 生成随机数，范围是0到总权重
    let random = Math.random() * totalWeight;
    let selectedDirection;

    // 根据权重选择方向
    for (const dir of availableDirections) {
      random -= dir.weight;
      if (random <= 0) {
        selectedDirection = dir;
        break;
      }
    }

    // 如果未选择到方向，使用第一个方向
    if (!selectedDirection) {
      selectedDirection = availableDirections[0];
    }

    // 保存当前选择的方向
    character.currentDirection = selectedDirection;

    // 根据选择的方向找到下一个十字路口，但必须在视口内
    const nextIntersection = this.findNextIntersectionInViewport(
      currentGridX,
      currentGridY,
      selectedDirection,
      mapWidth,
      mapHeight,
      edgeWidth
    );

    if (!nextIntersection) {
      // 没有找到下一个十字路口，稍后重试
      character.moveInterval = 500 + Math.random() * 1000;
      return false;
    }

    // 计算移动路径，考虑靠边行走
    const path = this.calculatePathToIntersection(
      currentGridX,
      currentGridY,
      nextIntersection.x,
      nextIntersection.y,
      selectedDirection,
      tileWidth,
      tileHeight
    );

    if (!path || path.length === 0) {
      // 计算路径失败，稍后重试
      character.moveInterval = 500 + Math.random() * 1000;
      return false;
    }

    // 设置路径点
    character.pathPoints = path;

    // 设置第一个路径点为目标
    const firstPoint = character.pathPoints.shift();
    character.targetX = firstPoint.x;
    character.targetY = firstPoint.y;
    character.isMoving = true;

    // 设置随机移动间隔
    character.moveInterval = 2000 + Math.random() * 3000; // 随机移动间隔 (2-5秒)

    // 更新网格位置
    character.targetGridX = nextIntersection.x;
    character.targetGridY = nextIntersection.y;

    // 更新位置映射
    this.characterPositions.delete(`${character.gridX},${character.gridY}`);
    this.characterPositions.set(`${nextIntersection.x},${nextIntersection.y}`, character);

    return true;
  }

  /**
   * 判断指定位置是否为十字路口
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为十字路口
   */
  isIntersection(gridX, gridY) {
    if (!window.roadNavigationGraph || !window.roadNavigationGraph.nodes) {
      return false;
    }

    // 当前位置必须是道路
    if (!this.isOnRoad(gridX, gridY)) {
      return false;
    }

    // 检查上下左右四个方向是否有道路
    const directions = [
      { dx: 0, dy: -1 }, // 上
      { dx: 1, dy: 0 },  // 右
      { dx: 0, dy: 1 },  // 下
      { dx: -1, dy: 0 }  // 左
    ];

    let roadCount = 0;

    for (const dir of directions) {
      const nx = gridX + dir.dx;
      const ny = gridY + dir.dy;

      if (this.isOnRoad(nx, ny)) {
        roadCount++;
      }
    }

    // 如果周围至少有3条道路，则认为是十字路口
    // 或者如果有2条不在同一直线上的道路，也认为是十字路口
    if (roadCount >= 3) {
      return true;
    } else if (roadCount === 2) {
      // 检查是否在同一直线上
      const hasHorizontalRoad = this.isOnRoad(gridX - 1, gridY) || this.isOnRoad(gridX + 1, gridY);
      const hasVerticalRoad = this.isOnRoad(gridX, gridY - 1) || this.isOnRoad(gridX, gridY + 1);

      // 如果水平和垂直方向都有路，则是十字路口
      return hasHorizontalRoad && hasVerticalRoad;
    }

    return false;
  }

  /**
   * 设置视口边界信息
   * @param {Object} viewportBounds 视口边界对象 {left, right, top, bottom}
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  setViewportBounds(viewportBounds, tileWidth, tileHeight) {
    this.viewportBounds = viewportBounds;
    this.viewportGridBounds = {
      left: Math.floor(viewportBounds.left / tileWidth),
      right: Math.ceil(viewportBounds.right / tileWidth),
      top: Math.floor(viewportBounds.top / tileHeight),
      bottom: Math.ceil(viewportBounds.bottom / tileHeight)
    };
  }

  /**
   * 寻找最近的十字路口
   * @param {number} startX 起始X坐标（网格）
   * @param {number} startY 起始Y坐标（网格）
   * @param {number} mapWidth 地图宽度（网格）
   * @param {number} mapHeight 地图高度（网格）
   * @param {number} edgeWidth 边缘宽度
   * @returns {Object|null} 最近的十字路口位置 {x, y}
   */
  findNearestIntersection(startX, startY, mapWidth, mapHeight, edgeWidth) {
    // 检查视口边界是否设置，如果没有设置，使用地图边界
    const viewportGridBounds = this.viewportGridBounds || {
      left: 0,
      right: mapWidth,
      top: 0,
      bottom: mapHeight
    };

    // 使用BFS寻找最近的十字路口
    const queue = [];
    const visited = new Set();

    // 将起点加入队列
    queue.push({ x: startX, y: startY, distance: 0 });
    visited.add(`${startX},${startY}`);

    // 四个方向：上、右、下、左
    const directions = [
      { dx: 0, dy: -1 },
      { dx: 1, dy: 0 },
      { dx: 0, dy: 1 },
      { dx: -1, dy: 0 }
    ];

    while (queue.length > 0) {
      const current = queue.shift();

      // 检查当前位置是否为十字路口
      if (this.isIntersection(current.x, current.y)) {
        // 检查是否在视口范围内（并留有一些边距）
        if (
          current.x >= viewportGridBounds.left + 2 && 
          current.x <= viewportGridBounds.right - 2 &&
          current.y >= viewportGridBounds.top + 2 && 
          current.y <= viewportGridBounds.bottom - 2
        ) {
          return { x: current.x, y: current.y };
        }
      }

      // 探索四个方向
      for (const dir of directions) {
        const nx = current.x + dir.dx;
        const ny = current.y + dir.dy;
        const key = `${nx},${ny}`;

        // 检查边界 - 限制在视口范围内搜索
        if (
          nx < viewportGridBounds.left || 
          nx > viewportGridBounds.right || 
          ny < viewportGridBounds.top || 
          ny > viewportGridBounds.bottom
        ) {
          continue;
        }

        // 检查是否已访问
        if (visited.has(key)) {
          continue;
        }

        // 检查是否是道路
        if (!this.isOnRoad(nx, ny)) {
          continue;
        }

        // 添加到队列
        queue.push({ x: nx, y: ny, distance: current.distance + 1 });
        visited.add(key);
      }

      // 如果搜索范围太大，限制搜索
      if (current.distance > 20) {
        break;
      }
    }

    return null; // 找不到十字路口
  }

  /**
   * 移动到指定的十字路口
   * @param {Object} character 人物对象
   * @param {Object} intersection 十字路口坐标
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  moveToIntersection(character, intersection, tileWidth, tileHeight) {
    // 计算像素坐标
    const targetX = intersection.x * tileWidth + tileWidth / 2;
    const targetY = intersection.y * tileHeight + tileHeight / 2;

    // 设置目标位置
    character.targetX = targetX;
    character.targetY = targetY;
    character.targetGridX = intersection.x;
    character.targetGridY = intersection.y;
    character.isMoving = true;

    // 设置移动间隔
    character.moveInterval = 2000 + Math.random() * 3000;

    // 更新位置映射
    this.characterPositions.delete(`${character.gridX},${character.gridY}`);
    this.characterPositions.set(`${intersection.x},${intersection.y}`, character);
  }

  /**
   * 获取可用的移动方向
   * @param {number} gridX 当前X坐标
   * @param {number} gridY 当前Y坐标
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @param {number} edgeWidth 边缘宽度
   * @param {Object} currentDirection 当前移动方向，用于计算调头概率
   * @returns {Array} 可用方向数组，元素为方向对象{dx,dy,name,weight}
   */
  getAvailableDirections(gridX, gridY, mapWidth, mapHeight, edgeWidth, currentDirection = null) {
    const directions = [
      { dx: 0, dy: -1, name: 'up' },    // 上
      { dx: 1, dy: 0, name: 'right' },  // 右
      { dx: 0, dy: 1, name: 'down' },   // 下
      { dx: -1, dy: 0, name: 'left' }   // 左
    ];

    // 筛选可用方向
    const availableDirections = [];

    for (const dir of directions) {
      const nx = gridX + dir.dx;
      const ny = gridY + dir.dy;

      // 检查是否在地图范围内并且不在边缘区域
      if (nx < edgeWidth || ny < edgeWidth || nx >= mapWidth - edgeWidth || ny >= mapHeight - edgeWidth) {
        continue;
      }

      // 检查相邻格子是否是道路
      if (this.isOnRoad(nx, ny)) {
        // 计算此方向的权重，默认权重为10
        let weight = 10;

        // 如果当前方向存在，判断是否为掉头方向
        if (currentDirection) {
          // 判断是否为掉头方向（方向相反）
          const isUTurn = dir.dx === -currentDirection.dx && dir.dy === -currentDirection.dy;

          if (isUTurn) {
            // 掉头方向的权重降低，只有2
            weight = 2;
          } else if (dir.dx === currentDirection.dx && dir.dy === currentDirection.dy) {
            // 继续当前方向的权重适中，为5
            weight = 5;
          }
          // 其他方向（转向）保持默认权重10
        }

        // 将方向和权重一起添加到可用方向列表
        availableDirections.push({
          ...dir,
          weight
        });
      }
    }

    return availableDirections;
  }

  /**
   * 沿指定方向寻找下一个十字路口
   * @param {number} startX 起点X坐标
   * @param {number} startY 起点Y坐标
   * @param {Object} direction 方向对象{dx,dy,name}
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @param {number} edgeWidth 边缘宽度
   * @returns {Object|null} 下一个十字路口坐标和接近该十字路口的路径点，如果找不到则返回null
   */
  findNextIntersection(startX, startY, direction, mapWidth, mapHeight, edgeWidth) {
    let x = startX + direction.dx;
    let y = startY + direction.dy;

    // 最大搜索距离
    const maxDistance = 30;
    let distance = 1;

    // 沿着当前方向搜索
    while (distance <= maxDistance) {
      // 检查边界
      if (x < edgeWidth || y < edgeWidth || x >= mapWidth - edgeWidth || y >= mapHeight - edgeWidth) {
        // 到达边缘区域，返回倒数第二个位置（避开边缘区域）
        if (distance > 1) {
          return {
            x: x - direction.dx,
            y: y - direction.dy,
            pathToIntersection: [] // 空路径，将在calculatePathToIntersection中生成
          };
        }
        return null;
      }

      // 检查是否是道路
      if (!this.isOnRoad(x, y)) {
        // 已经不在道路上了，返回最后一个道路位置
        if (distance > 1) {
          return {
            x: x - direction.dx,
            y: y - direction.dy,
            pathToIntersection: [] // 空路径，将在calculatePathToIntersection中生成
          };
        }
        return null;
      }

      // 检查是否是十字路口
      if (this.isIntersection(x, y)) {
        // 提前判断下一步方向
        return {
          x,
          y,
          pathToIntersection: [] // 空路径，将在calculatePathToIntersection中生成
        };
      }

      // 继续沿着当前方向移动
      x += direction.dx;
      y += direction.dy;
      distance++;
    }

    // 如果达到最大搜索距离仍未找到十字路口
    // 返回最后一个有效位置
    return {
      x: x - direction.dx,
      y: y - direction.dy,
      pathToIntersection: [] // 空路径，将在calculatePathToIntersection中生成
    };
  }

  /**
   * 计算从当前位置到目标十字路口的路径，考虑靠边行走
   * @param {number} startX 起点X坐标
   * @param {number} startY 起点Y坐标
   * @param {number} endX 终点X坐标
   * @param {number} endY 终点Y坐标
   * @param {Object} direction 移动方向
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array} 路径点数组，每个点包含{x,y}像素坐标
   */
  calculatePathToIntersection(startX, startY, endX, endY, direction, tileWidth, tileHeight) {
    const path = [];

    // 确定移动方向
    const isHorizontal = direction.dx !== 0;
    const isVertical = direction.dy !== 0;

    // 计算从起点到终点的路径
    if (isHorizontal) {
      // 水平移动（左右）
      const y = startY;
      const offset = direction.dx > 0 ? 0.3 : -0.3; // 右走靠下，左走靠上

      // 从起点到终点前一格，每格都添加一个路径点
      let x = startX;
      const step = direction.dx > 0 ? 1 : -1;

      // 判断是否接近终点
      const isNearEnd = Math.abs(endX - startX) <= 2;

      // 如果不是很接近终点，正常走完全程
      if (!isNearEnd) {
        while (x !== endX) {
          x += step;

          // 检查该位置是否是道路
          if (!this.isOnRoad(x, y)) {
            break;
          }

          // 距离终点两格时，开始准备下一个转向方向
          const distanceToEnd = Math.abs(endX - x);
          if (distanceToEnd <= 1) {
            // 提前计算下一步可能的方向
            const nextDirections = this.getAvailableDirections(endX, endY,
              Math.max(endX * 2, 100), Math.max(endY * 2, 100), 6, direction);

            // 如果有可用方向，随机加权选择一个
            if (nextDirections.length > 0) {
              // 计算总权重
              const totalWeight = nextDirections.reduce((sum, dir) => sum + dir.weight, 0);

              // 生成随机数，范围是0到总权重
              let random = Math.random() * totalWeight;
              let selectedDirection = nextDirections[0];

              // 根据权重选择方向
              for (const dir of nextDirections) {
                random -= dir.weight;
                if (random <= 0) {
                  selectedDirection = dir;
                  break;
                }
              }

              // 添加转向路径点
              // 在终点前一格，添加向新方向偏移的路径点
              if (isVertical || selectedDirection.dy !== 0) {
                // 如果新方向是垂直的，调整水平偏移
                const horizontalOffset = selectedDirection.dx === 1 ? 0.2 :
                  (selectedDirection.dx === -1 ? -0.2 : 0);

                path.push({
                  x: endX * tileWidth + tileWidth / 2 + horizontalOffset * tileWidth,
                  y: y * tileHeight + tileHeight / 2 + offset * tileHeight
                });
              } else {
                // 如果新方向是水平的，调整垂直偏移
                const verticalOffset = selectedDirection.dy === 1 ? 0.2 :
                  (selectedDirection.dy === -1 ? -0.2 : 0);

                path.push({
                  x: endX * tileWidth + tileWidth / 2,
                  y: y * tileHeight + tileHeight / 2 + offset * tileHeight + verticalOffset * tileHeight
                });
              }
            }
          } else {
            // 正常的路径点
            path.push({
              x: x * tileWidth + tileWidth / 2,
              y: y * tileHeight + tileHeight / 2 + offset * tileHeight
            });
          }
        }
      }
    } else if (isVertical) {
      // 垂直移动（上下）
      const x = startX;
      const offset = direction.dy > 0 ? -0.3 : 0.3; // 下走靠左，上走靠右

      // 从起点到终点，每格都添加一个路径点
      let y = startY;
      const step = direction.dy > 0 ? 1 : -1;

      // 判断是否接近终点
      const isNearEnd = Math.abs(endY - startY) <= 2;

      // 如果不是很接近终点，正常走完全程
      if (!isNearEnd) {
        while (y !== endY) {
          y += step;

          // 检查该位置是否是道路
          if (!this.isOnRoad(x, y)) {
            break;
          }

          // 距离终点两格时，开始准备下一个转向方向
          const distanceToEnd = Math.abs(endY - y);
          if (distanceToEnd <= 1) {
            // 提前计算下一步可能的方向
            const nextDirections = this.getAvailableDirections(endX, endY,
              Math.max(endX * 2, 100), Math.max(endY * 2, 100), 6, direction);

            // 如果有可用方向，随机加权选择一个
            if (nextDirections.length > 0) {
              // 计算总权重
              const totalWeight = nextDirections.reduce((sum, dir) => sum + dir.weight, 0);

              // 生成随机数，范围是0到总权重
              let random = Math.random() * totalWeight;
              let selectedDirection = nextDirections[0];

              // 根据权重选择方向
              for (const dir of nextDirections) {
                random -= dir.weight;
                if (random <= 0) {
                  selectedDirection = dir;
                  break;
                }
              }

              // 添加转向路径点
              // 在终点前一格，添加向新方向偏移的路径点
              if (isHorizontal || selectedDirection.dx !== 0) {
                // 如果新方向是水平的，调整垂直偏移
                const verticalOffset = selectedDirection.dy === 1 ? 0.2 :
                  (selectedDirection.dy === -1 ? -0.2 : 0);

                path.push({
                  x: x * tileWidth + tileWidth / 2 + offset * tileWidth,
                  y: endY * tileHeight + tileHeight / 2 + verticalOffset * tileHeight
                });
              } else {
                // 如果新方向是垂直的，调整水平偏移
                const horizontalOffset = selectedDirection.dx === 1 ? 0.2 :
                  (selectedDirection.dx === -1 ? -0.2 : 0);

                path.push({
                  x: x * tileWidth + tileWidth / 2 + offset * tileWidth + horizontalOffset * tileWidth,
                  y: endY * tileHeight + tileHeight / 2
                });
              }
            }
          } else {
            // 正常的路径点
            path.push({
              x: x * tileWidth + tileWidth / 2 + offset * tileWidth,
              y: y * tileHeight + tileHeight / 2
            });
          }
        }
      }
    }

    // 最后添加目标十字路口位置
    path.push({
      x: endX * tileWidth + tileWidth / 2,
      y: endY * tileHeight + tileHeight / 2
    });

    return path;
  }

  /**
   * 判断指定位置是否为道路
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为道路
   */
  isOnRoad(gridX, gridY) {
    // 使用全局道路数据检查位置
    if (!window.roadNavigationGraph || !window.roadNavigationGraph.nodes) {
      return false;
    }

    // 检查该位置是否存在于道路节点中
    return window.roadNavigationGraph.nodes[`${gridX}_${gridY}`] !== undefined;
  }

  /**
   * 在室内随机移动
   * @param {Object} character 人物数据
   */
  moveRandomInRoom(character) {
    // 检查角色是否被鼠标悬停暂停
    if (character.isPausedByHover) {
      return;
    }

    if (!character.bounds || !character.isIndoor) {
      console.warn(`无法进行室内随机移动: ${character.id}`, character);
      return;
    }

    const { minX, maxX, minY, maxY } = character.bounds;

    // 生成在边界内的随机目标位置
    const targetX = Math.random() * (maxX - minX) + minX;
    const targetY = Math.random() * (maxY - minY) + minY;

    // // console.log(`角色${character.id}在室内随机移动，目标:`, targetX, targetY);

    // 设置新的目标位置
    character.targetX = targetX;
    character.targetY = targetY;
    character.isMoving = true;

    // 确保角色精灵朝向正确
    if (character.sprite) {
      const isMovingRight = targetX > character.sprite.x;
      character.sprite.scale.x = isMovingRight ? -1 : 1;
    }

    // 启动动画（如果有）
    if (character.animatedSprite && !character.animatedSprite.playing) {
      character.animatedSprite.play();
    }
  }

  /**
   * 更新工作中的角色
   * @param {Object} character 角色对象
   * @param {number} deltaTime 时间增量
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  updateWorkingCharacter(character, deltaTime, tileWidth, tileHeight) {
    // 检查角色是否被鼠标悬停暂停
    if (character.isPausedByHover) {
      return;
    }

    // 调用moveToWork设置移动目标和状态
    const hasReachedTarget = this.moveToWork(character, deltaTime);

    // 如果目标已设置但未到达，需要执行移动逻辑 
    if (!hasReachedTarget && character.isMoving) {
      // 启动动画
      if (character.animatedSprite && !character.animatedSprite.playing) {
        character.animatedSprite.play();
      }

      // 执行实际移动
      this.moveCharacterToTarget(character, deltaTime, tileWidth, tileHeight);
    }
  }

  /**
   * 更新移动中的角色
   * @param {Object} character 角色对象
   * @param {number} deltaTime 时间增量
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  updateMovingCharacter(character, deltaTime, tileWidth, tileHeight) {
    // 检查角色是否被鼠标悬停暂停
    if (character.isPausedByHover) {
      return;
    }

    // 获取游戏状态store
    const gameStore = useGameStore();

    // 如果角色正在寻找建筑物或已经在前往建筑的路上，不更新计时器
    if (!character.isSearchingBuilding && !character.isGoingToBuilding) {
      // 更新道路行走时间计时器
      character.roadWalkingTime = (character.roadWalkingTime || 0) + deltaTime;

      // 获取室外和总人物数量
      const totalPopulation = gameStore.populationTotal || 0;
      const outdoorPopulation = gameStore.populationOutdoor || 0;

      // 检查室外人物数量是否足够（必须大于总人口的一半）
      const canEnterBuilding = outdoorPopulation > totalPopulation / 2;

      // 检查是否达到寻找建筑的时间阈值（增加到30秒，并且不除以游戏速度）
      const searchBuildingThreshold = 30; // 增加为30秒

      if (character.roadWalkingTime >= searchBuildingThreshold && canEnterBuilding) {
        // 重置计时器
        character.roadWalkingTime = 0;

        // 开始寻找附近的建筑物
        character.isSearchingBuilding = true;

        // 获取当前网格坐标
        const currentGridX = Math.floor(character.x / tileWidth);
        const currentGridY = Math.floor(character.y / tileHeight);

        // 寻找附近的建筑物
        const nearbyBuilding = this.searchNearbyBuildings(
          currentGridX,
          currentGridY,
          character.currentDirection,
          tileWidth,
          tileHeight
        );

        if (nearbyBuilding) {
          // 找到建筑物，设置为目标
          character.isGoingToBuilding = true;
          character.targetBuilding = nearbyBuilding;

          // 计算到建筑物的路径
          this.calculatePathToBuilding(
            character,
            nearbyBuilding,
            tileWidth,
            tileHeight
          );

        } else {
          // 没找到建筑物，继续移动
          character.isSearchingBuilding = false;
        }
      } else if (character.roadWalkingTime >= searchBuildingThreshold && !canEnterBuilding) {
        // 当室外人数不足时，仅重置计时器，不执行进入建筑逻辑
        character.roadWalkingTime = 0;
        console.log(`角色${character.id}想进入建筑，但室外人数不足(${outdoorPopulation}/${totalPopulation})，无法进入`);
      }
    }

    // 启动动画
    if (character.animatedSprite && !character.animatedSprite.playing) {
      character.animatedSprite.play();
    }

    // 执行移动
    this.moveCharacterToTarget(character, deltaTime, tileWidth, tileHeight);
  }

  /**
   * 搜索角色附近的建筑物
   * @param {number} gridX 角色当前X网格坐标
   * @param {number} gridY 角色当前Y网格坐标
   * @param {Object} direction 角色当前移动方向
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Object|null} 找到的建筑物对象，如果没找到则返回null
   */
  searchNearbyBuildings(gridX, gridY, direction, tileWidth, tileHeight) {
    // 获取游戏状态store和建筑数据
    const gameStore = useGameStore();
    const buildings = gameStore.buildings;
    
    // 如果没有建筑物数据，无法进行搜索
    if (!buildings || buildings.length === 0) {
      console.warn("没有可用的建筑物数据");
      return null;
    }

    // 增加随机概率，使角色有20%的机会搜索建筑物(降低概率)
    if (Math.random() > 0.2) {
      return null;
    }

    if (!direction) return null;

    // 定义搜索范围（网格单位）
    const searchRange = 5; // 增加搜索范围从3到5

    // 创建建筑物候选列表
    const buildingCandidates = [];

    // 根据移动方向确定搜索方向
    const isHorizontal = direction.dx !== 0;
    const isMovingDown = direction.dy > 0; // 判断是否向下移动
    
    // 水平移动时，绝不搜索下方建筑物
    if (isHorizontal) {
      // 水平移动（左右），只搜索上方向的建筑物
      for (let offsetY = -searchRange; offsetY < 0; offsetY++) {
        // Y必须小于0，确保只搜索上方建筑
        for (let offsetX = -searchRange; offsetX <= searchRange; offsetX++) {
          const checkX = gridX + offsetX;
          const checkY = gridY + offsetY;

          // 检查该位置是否有建筑物
          const gridKey = `${checkX},${checkY}`;
          if (gameStore.buildingData.has(gridKey)) {
            const buildingId = gameStore.buildingData.get(gridKey);

            // 获取建筑物数据
            const building = buildings.find(b => b.buildingId === buildingId);
            if (building) {
              // 只考虑house类型的建筑物
              if (building.style !== 'house') {
                continue;
              }

              // 计算建筑物中心点到角色的距离
              const distance = Math.sqrt(offsetX * offsetX + offsetY * offsetY);

              // 如果已经存在相同ID的建筑，不重复添加
              if (!buildingCandidates.some(candidate => candidate.building.buildingId === buildingId)) {
                // 将建筑物添加到候选列表
                buildingCandidates.push({
                  building,
                  distance,
                  gridX: checkX,
                  gridY: checkY
                });
              }
            }
          }
        }
      }
    } else {
      // 垂直移动（上下）
      // 如果向下移动，只搜索左右方向的建筑物
      // 如果向上移动，搜索左右和上方的建筑物
      
      const minY = isMovingDown ? 0 : -searchRange; // 向下移动时不搜索下方
      const maxY = isMovingDown ? 0 : -1; // 向下移动时y偏移最大为0（不包括）
      
      for (let offsetX = -searchRange; offsetX <= searchRange; offsetX++) {
        // 跳过当前列
        if (offsetX === 0) continue;

        // 搜索合适的Y方向范围
        for (let offsetY = minY; offsetY <= maxY; offsetY++) {
          // 向下移动时，必须确保Y=0（水平搜索）
          if (isMovingDown && offsetY !== 0) continue;
          
          const checkX = gridX + offsetX;
          const checkY = gridY + offsetY;

          // 检查该位置是否有建筑物
          const gridKey = `${checkX},${checkY}`;
          if (gameStore.buildingData.has(gridKey)) {
            const buildingId = gameStore.buildingData.get(gridKey);

            // 获取建筑物数据
            const building = buildings.find(b => b.buildingId === buildingId);
            if (building) {
              // 只考虑house类型的建筑物
              if (building.style !== 'house') {
                continue;
              }

              // 计算建筑物中心点到角色的距离
              const distance = Math.sqrt(offsetX * offsetX + offsetY * offsetY);

              // 如果已经存在相同ID的建筑，不重复添加
              if (!buildingCandidates.some(candidate => candidate.building.buildingId === buildingId)) {
                // 将建筑物添加到候选列表
                buildingCandidates.push({
                  building,
                  distance,
                  gridX: checkX,
                  gridY: checkY
                });
              }
            }
          }
        }
      }
    }

    // 如果有候选建筑物，根据距离和随机因素选择一个
    if (buildingCandidates.length > 0) {
      // 按距离排序
      buildingCandidates.sort((a, b) => a.distance - b.distance);

      // 选择最近的几个建筑物中的一个（引入随机性）
      const candidateCount = Math.min(3, buildingCandidates.length);
      const selectedIndex = Math.floor(Math.random() * candidateCount);

      const selectedBuilding = buildingCandidates[selectedIndex].building;
      
      // 记录日志，输出方向信息
      const directionInfo = isHorizontal 
        ? `水平移动(dx=${direction.dx})` 
        : `垂直移动(dy=${direction.dy})`;
      // console.log(`${directionInfo} - 选择建筑，类型: ${selectedBuilding.style}，ID: ${selectedBuilding.buildingId}`);

      return selectedBuilding;
    }

    return null;
  }

  /**
   * 计算人物到建筑物的移动路径
   * @param {Object} character 角色对象
   * @param {Object} building 建筑物对象
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  calculatePathToBuilding(character, building, tileWidth, tileHeight) {
    // 安全检查
    if (!building || !building.sprite) {
      console.warn('无法计算到建筑物的路径：建筑物对象无效');
      character.isGoingToBuilding = false;
      character.isSearchingBuilding = false;
      return;
    }

    // 计算建筑物正门位置（默认为底部中心）
    const buildingSprite = building.sprite;
    let entranceX, entranceY;
    // console.log('buildingSprite:', buildingSprite);
    // 检查建筑物是否定义了明确的入口位置
    if (buildingSprite.entranceX !== undefined && buildingSprite.entranceY !== undefined) {
      // 使用预定义的入口位置
      entranceX = buildingSprite.entranceX;
      entranceY = buildingSprite.entranceY;
    } else {
      // 使用建筑物底部中心外部作为默认入口
      // X坐标为建筑物水平中心
      entranceX = buildingSprite.x +
        (buildingSprite.width) / 2;

      // Y坐标为建筑物底部外侧（底部边缘 + 1格）
      entranceY = (buildingSprite.buildingGridY + buildingSprite.buildingGridHeight) * tileHeight + tileHeight / 2;

      // 确保入口点不是障碍物
      const entranceGridX = Math.floor(entranceX / tileWidth);
      const entranceGridY = Math.floor(entranceY / tileHeight);

      // 如果入口点是障碍物，尝试调整
      if (this.isObstacle(entranceGridX, entranceGridY)) {
        // 沿建筑物底部找一个可用的入口点
        for (let offsetX = -1; offsetX <= 1; offsetX++) {
          const testX = entranceGridX + offsetX;
          const testY = entranceGridY;

          if (!this.isObstacle(testX, testY)) {
            entranceX = testX * tileWidth + tileWidth / 2;
            break;
          }

          // 如果水平调整无效，尝试向下移动一格
          if (offsetX === 1 && this.isObstacle(testX, testY)) {
            if (!this.isObstacle(entranceGridX, entranceGridY + 1)) {
              entranceY = (entranceGridY + 1) * tileHeight + tileHeight / 2;
            }
          }
        }
      }
    }

    // 记录计算出的入口位置
    // console.log(`建筑${building.id}的入口位置: (${entranceX}, ${entranceY})`);

    // 将入口位置转换为网格坐标
    const entranceGridX = Math.floor(entranceX / tileWidth);
    const entranceGridY = Math.floor(entranceY / tileHeight);

    // 计算角色当前位置的网格坐标
    const startGridX = Math.floor(character.x / tileWidth);
    const startGridY = Math.floor(character.y / tileHeight);

    // console.log(`计算从(${startGridX},${startGridY})到建筑物入口(${entranceGridX},${entranceGridY})的路径`);

    // 寻找最近的道路点，作为可能的接近点
    let nearestRoadX = -1, nearestRoadY = -1, nearestRoadDistance = Infinity;

    // 以建筑入口为中心，扩大搜索范围至10格
    const searchRange = 10;

    // 定义入口前的可达位置（正门前的有效站立点）
    // 检查入口周围的8个方向，找到一个没有障碍物的位置作为最终目标点
    const directions = [
      { dx: 0, dy: 1 },  // 下
      { dx: -1, dy: 1 }, // 左下
      { dx: 1, dy: 1 },  // 右下
      { dx: -1, dy: 0 }, // 左
      { dx: 1, dy: 0 },  // 右
      { dx: 0, dy: -1 }, // 上
      { dx: -1, dy: -1 }, // 左上
      { dx: 1, dy: -1 }   // 右上
    ];

    // 首先找到所有可能的临近路点
    const roadPoints = [];

    // 从建筑入口向外搜索，找到所有可达的道路点
    for (let distance = 1; distance <= searchRange; distance++) {
      for (let dx = -distance; dx <= distance; dx++) {
        for (let dy = -distance; dy <= distance; dy++) {
          // 只检查当前"环"上的点
          if (Math.abs(dx) === distance || Math.abs(dy) === distance) {
            const checkX = entranceGridX + dx;
            const checkY = entranceGridY + dy;

            // 检查是否是道路且不是障碍物
            if (this.isOnRoad(checkX, checkY) && !this.isObstacle(checkX, checkY)) {
              // 计算到入口的曼哈顿距离
              const distToEntrance = Math.abs(dx) + Math.abs(dy);

              roadPoints.push({
                x: checkX,
                y: checkY,
                distance: distToEntrance
              });

              // 更新最近的道路点
              if (distToEntrance < nearestRoadDistance) {
                nearestRoadX = checkX;
                nearestRoadY = checkY;
                nearestRoadDistance = distToEntrance;
              }
            }
          }
        }
      }

      // 如果已经找到一些道路点，不需要继续搜索太远
      if (roadPoints.length >= 5) {
        break;
      }
    }

    // 如果找不到任何道路点，尝试寻找任何无障碍点
    if (roadPoints.length === 0) {
      // console.log('无法找到建筑物附近的道路点，尝试寻找任何无障碍点');

      // 在建筑物入口周围扩展搜索范围
      for (let distance = 1; distance <= searchRange; distance++) {
        let foundAccessPoint = false;

        for (const dir of directions) {
          const checkX = entranceGridX + dir.dx * distance;
          const checkY = entranceGridY + dir.dy * distance;

          // 检查该位置是否没有障碍物且可到达
          if (!this.isObstacle(checkX, checkY)) {
            // 设置找到的无障碍点作为目标
            nearestRoadX = checkX;
            nearestRoadY = checkY;
            foundAccessPoint = true;
            break;
          }
        }

        if (foundAccessPoint) {
          break;
        }
      }
    }

    // 如果仍找不到可达点，报错并中止
    if (nearestRoadX === -1 || nearestRoadY === -1) {
      console.warn('无法找到建筑物入口前的可达位置，建筑可能被完全包围');
      character.isGoingToBuilding = false;
      character.isSearchingBuilding = false;
      return;
    }

    // 设置目标点
    const targetGridX = nearestRoadX;
    const targetGridY = nearestRoadY;

    // console.log(`为建筑${building.buildingId}找到最佳接近点：(${targetGridX}, ${targetGridY})`);

    // 开始计算从角色到建筑的路径
    let pathToBuilding = null;

    // 直接计算从当前位置到建筑接近点的路径
    pathToBuilding = this.findPath(
      startGridX,
      startGridY,
      targetGridX,
      targetGridY,
      tileWidth,
      tileHeight
    );

    // 如果没有找到直接路径，尝试使用两段式路径
    if (!pathToBuilding || pathToBuilding.length === 0) {
      // console.log('无法找到直接路径，尝试两段式路径...');

      // 找到角色最近的道路点
      const characterNearestRoad = this.findNearestRoadPoint(startGridX, startGridY);

      if (characterNearestRoad) {
        // 先计算从当前位置到最近道路点的路径
        const pathToRoad = this.findPath(
          startGridX,
          startGridY,
          characterNearestRoad.x,
          characterNearestRoad.y,
          tileWidth,
          tileHeight
        );

        if (pathToRoad && pathToRoad.length > 0) {
          // 再计算从道路点到建筑物接近点的路径
          const pathFromRoadToBuilding = this.findPath(
            characterNearestRoad.x,
            characterNearestRoad.y,
            targetGridX,
            targetGridY,
            tileWidth,
            tileHeight
          );

          if (pathFromRoadToBuilding && pathFromRoadToBuilding.length > 0) {
            // 合并路径
            pathToBuilding = [...pathToRoad, ...pathFromRoadToBuilding];
          }
        }
      }
    }

    // 如果仍然没有找到路径，尝试简单的直线路径（即使可能无法到达）
    if (!pathToBuilding || pathToBuilding.length === 0) {
      // console.warn('无法计算到建筑物入口的路径，使用简单直线路径');

      // 创建一个简单的路径点
      pathToBuilding = [
        {
          x: targetGridX * tileWidth + tileWidth / 2,
          y: targetGridY * tileHeight + tileHeight / 2
        }
      ];
    }

    // 添加最后一步：从接近点到实际入口
    const finalStep = {
      x: entranceX,
      y: entranceY - tileHeight / 4 // 稍微离建筑物上方一点
    };

    // 设置完整路径
    character.pathPoints = [...pathToBuilding, finalStep];

    // console.log(`已计算路径，共${character.pathPoints.length}个点，从(${startGridX},${startGridY})到建筑物(${entranceGridX},${entranceGridY})`);

    // 设置第一个路径点为目标
    if (character.pathPoints.length > 0) {
      const firstPoint = character.pathPoints.shift();
      character.targetX = firstPoint.x;
      character.targetY = firstPoint.y;
    }
  }

  /**
   * 查找距离指定位置最近的道路点
   * @param {number} targetX 目标位置X坐标
   * @param {number} targetY 目标位置Y坐标
   * @returns {Object|null} 最近的道路点坐标，如果没找到则返回null
   */
  findNearestRoadPoint(targetX, targetY) {
    // 最大搜索轮数
    const maxRounds = 10;
    
    // 存储所有找到的道路点及其距离
    const roadPoints = [];
    
    // 采用轮询方式搜索：左->下->右->上
    // 对于左、下、右方向，距离范围为n+2
    // 对于上方向，距离范围为n
    // n是轮数
    
    // 搜索方向顺序
    const directions = [
      { name: "左", dx: -1, dy: 0, extraRange: 2 },
      { name: "下", dx: 0, dy: 1, extraRange: 2 },
      { name: "右", dx: 1, dy: 0, extraRange: 2 },
      { name: "上", dx: 0, dy: -1, extraRange: 0 }
    ];
    
    // 按轮数进行搜索
    for (let round = 1; round <= maxRounds; round++) {
      let foundPointInRound = false;
      
      // 对每个方向进行搜索
      for (const dir of directions) {
        // 计算当前方向的搜索范围
        const searchRange = round + dir.extraRange;
        
        // 根据方向生成搜索区域
        for (let distance = 1; distance <= searchRange; distance++) {
          if (dir.dx !== 0) {
            // 水平方向搜索（左右）
            const checkX = targetX + dir.dx * distance;
            const checkY = targetY;
            
            // 检查是否是道路
            if (this.isOnRoad(checkX, checkY)) {
              roadPoints.push({
                x: checkX,
                y: checkY,
                distance: distance,  // 直线方向保持原始距离
                round: round,
                direction: dir.name,
                priority: directions.indexOf(dir) + 1, // 优先级基于方向顺序
                isDiagonal: false // 标记为非对角线方向
              });
              
              foundPointInRound = true;
              break; // 找到该方向的点后，不再继续增加距离
            }
          } else if (dir.dy !== 0) {
            // 垂直方向搜索（上下）
            // 首先检查正垂直方向(优先级最高)
            const checkX = targetX;
            const checkY = targetY + dir.dy * distance;
            
            // 检查正垂直方向是否是道路
            if (this.isOnRoad(checkX, checkY)) {
              roadPoints.push({
                x: checkX,
                y: checkY,
                distance: distance, // 直线方向保持原始距离
                round: round,
                direction: dir.name,
                priority: directions.indexOf(dir) + 1,
                isDiagonal: false // 标记为非对角线方向
              });
              
              foundPointInRound = true;
              break; // 找到了点，跳出循环
            }
            
            // 如果正方向没找到，再扩展到斜角方向搜索
            let foundDiagonal = false;
            
            // 对于垂直方向，同时考虑附近的左右格子，形成一个扇形搜索区域
            for (let offsetX = -distance; offsetX <= distance; offsetX++) {
              if (offsetX === 0) continue; // 跳过正中间的列（已经检查过）
              
              const checkX = targetX + offsetX;
              const checkY = targetY + dir.dy * distance;
              
              // 检查是否是道路
              if (this.isOnRoad(checkX, checkY)) {
                // 计算真实距离
                let realDistance = Math.sqrt(offsetX * offsetX + distance * distance);
                
                // 为斜角位置增加1.5倍的距离权重，降低其优先级
                realDistance *= 1.5;
                
                roadPoints.push({
                  x: checkX,
                  y: checkY,
                  distance: realDistance, // 斜角方向距离增加1.5倍
                  round: round,
                  direction: dir.name + (offsetX < 0 ? "左" : offsetX > 0 ? "右" : ""),
                  priority: directions.indexOf(dir) + 1, // 优先级基于方向顺序
                  isDiagonal: true // 标记为对角线方向
                });
                
                foundDiagonal = true;
                break; // 找到一个斜角方向就退出
              }
            }
            
            if (foundDiagonal) {
              foundPointInRound = true;
              break; // 找到了点，跳出循环
            }
          }
        }
        
        // 如果在当前方向找到了道路点，跳转到下一个方向
        if (foundPointInRound) break;
      }
      
      // 在本轮中找到了道路点，按优先级和距离排序并返回最佳点
      if (roadPoints.length > 0) {
        roadPoints.sort((a, b) => {
          // 首先按轮数排序
          if (a.round !== b.round) {
            return a.round - b.round;
          }
          
          // 轮数相同时按优先级排序（左下右上的顺序）
          if (a.priority !== b.priority) {
            return a.priority - b.priority;
          }
          
          // 优先级相同时，优先考虑非对角线方向
          if (a.isDiagonal !== b.isDiagonal) {
            return a.isDiagonal ? 1 : -1; // 非对角线方向优先
          }
          
          // 最后按距离排序
          return a.distance - b.distance;
        });
        
        const bestPoint = roadPoints[0];
        const diagonalInfo = bestPoint.isDiagonal ? "(斜角)" : "(直线)";
        // console.log(`第${bestPoint.round}轮找到${roadPoints.length}个道路点，选择${bestPoint.direction}${diagonalInfo}方向，距离: ${bestPoint.distance.toFixed(2)}`);
        
        return { x: bestPoint.x, y: bestPoint.y };
      }
    }
    
    // 应急情况：如果以上策略未找到任何道路点
    // 检查当前位置是否是道路
    if (this.isOnRoad(targetX, targetY)) {
      console.log(`未找到远处道路点，当前位置是道路，选择原地停留`);
      return { x: targetX, y: targetY };
    }
    
    // 尝试周围8个方向的任意一个非障碍物点
    const emergencyDirections = [
      { dx: -1, dy: 0, name: "左" },
      { dx: 0, dy: 1, name: "下" },
      { dx: 1, dy: 0, name: "右" },
      { dx: 0, dy: -1, name: "上" },
      { dx: -1, dy: 1, name: "左下" },
      { dx: 1, dy: 1, name: "右下" },
      { dx: -1, dy: -1, name: "左上" },
      { dx: 1, dy: -1, name: "右上" }
    ];
    
    // 按照左下右上的优先级排序，优先考虑非对角线方向
    emergencyDirections.sort((a, b) => {
      // 优先上下左右方向
      const aIsStraight = a.dx === 0 || a.dy === 0;
      const bIsStraight = b.dx === 0 || b.dy === 0;
      
      if (aIsStraight && !bIsStraight) return -1;
      if (!aIsStraight && bIsStraight) return 1;
      
      // 下和右优先于上和左
      if (a.dy > 0 || a.dx > 0) return -1;
      if (b.dy > 0 || b.dx > 0) return 1;
      
      return 0;
    });
    
    for (const dir of emergencyDirections) {
      const checkX = targetX + dir.dx;
      const checkY = targetY + dir.dy;
      
      if (!this.isObstacle(checkX, checkY)) {
        const diagonalInfo = (dir.dx !== 0 && dir.dy !== 0) ? "(斜角)" : "(直线)";
        console.log(`应急移动：选择${dir.name}${diagonalInfo}方向的非障碍点`);
        return { x: checkX, y: checkY };
      }
    }
    
    console.warn(`在所有搜索策略下均未找到可行点，角色将无法移动`);
    return null;
  }

  /**
   * 让角色进入建筑
   * @param {Object} character 角色对象
   * @param {Object} building 建筑对象
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  enterBuilding(character, building, tileWidth, tileHeight) {
    // console.log(`角色${character.id}尝试进入建筑${building.buildingId}`, building);

    // 检查建筑类型和建筑物
    if (!building || !building.floors || building.floors.length === 0) {
      console.warn(`建筑${building.buildingId}没有有效的楼层`);
      this.resetCharacterBuildingState(character);
      return;
    }

    // 设置角色状态
    character.isEnteringBuilding = true;
    // console.log('building.floors', building);
    // 为简单起见，选择第一个楼层
    const targetFloorIndex = building.sprite.children.length - 1;
    const targetFloor = building.sprite.children[targetFloorIndex];

    // 检查建筑物是否有楼层
    if (!targetFloor) {
      console.warn(`角色${character.id}找不到可进入的楼层`);
      this.resetCharacterBuildingState(character);
      return;
    }

    // 获取室内地板精灵
    if (!targetFloor.room) {
      console.warn('选择的楼层没有室内地板');
      this.resetCharacterBuildingState(character);
      return;
    }

    const roomSprite = targetFloor.room;

    // 确保角色有有效的sprite对象
    if (!character.sprite) {
      console.warn('角色没有有效的sprite对象');
      this.resetCharacterBuildingState(character);
      return;
    }

    // 记录原始尺寸（如果未记录）
    if (!character.originalWidth) {
      character.originalWidth = character.sprite.width;
      character.originalHeight = character.sprite.height;
    }

    // console.log('进入房间前的状态:', roomSprite);

    // 使用直接引用
    const characterSprite = character.sprite;

    // 首先从当前父容器中移除精灵(如果已经有父容器)
    if (characterSprite.parent) {
      // console.log(`从父容器${characterSprite.parent.name || '未命名容器'}中移除角色精灵`);
      characterSprite.parent.removeChild(characterSprite);
    }

    // 更新角色状态
    character.isMoving = false;
    character.isIndoor = true;
    characterSprite.isIndoor = true;

    // 将精灵位置设置为室内地板中心点
    characterSprite.x = roomSprite.width / 2;
    characterSprite.y = roomSprite.height;

    // 设置角色在室内的活动范围
    character.bounds = {
      minX: roomSprite.width * 0.1,
      maxX: roomSprite.width * 0.9,
      minY: roomSprite.height * 0.5,
      maxY: roomSprite.height * 0.9
    };

    // 确保室内容器已初始化
    if (!roomSprite.indoorCharacters) {
      roomSprite.indoorCharacters = [];
    }
    // 更新角色建筑状态
    character.isEnteringBuilding = false;
    character.isGoingToBuilding = false;
    character.isSearchingBuilding = false;
    character.currentBuilding = building.sprite;
    character.currentFloor = targetFloor;
    character.currentRoom = roomSprite;
    character.buildingId = building.buildingId;

    // 设置室内停留时间（10-20秒）
    character.buildingStayTime = 0;
    character.indoorStayTime = 10 + Math.random() * 10;
    character.indoorMovementTimer = 0;  // 初始化移动计时器

    // 设置目标位置为当前位置，确保不会有未完成的移动
    character.targetX = characterSprite.x;
    character.targetY = characterSprite.y;
    // 将角色精灵添加到室内地板容器
    roomSprite.addChild(characterSprite);

    // 存储角色到indoor characters数组
    if (!roomSprite.indoorCharacters.includes(character)) {
      roomSprite.indoorCharacters.push(character);
    }



    // 立刻触发一次室内随机移动
    this.moveRandomInRoom(character);

    // 将角色添加到建筑物的室内角色数组中
    if (!building.indoorCharacters) {
      building.indoorCharacters = [];
    }
    building.indoorCharacters.push(character);

    // 更新室外人物计数
    const gameStore = useGameStore();
    gameStore.populationOutdoor = Math.max(0, (gameStore.populationOutdoor || 0) - 1);
    // console.log(`角色${character.id}进入建筑，室外人物总数减少为: ${gameStore.populationOutdoor}`);

    // 更新角色状态
    character.isIndoor = true;

    // console.log(`角色${character.id}已成功进入建筑${building.buildingId}的楼层${targetFloorIndex}`);
  }

  /**
   * 重置角色的建筑物相关状态
   * @param {Object} character 角色对象
   */
  resetCharacterBuildingState(character) {
    character.isEnteringBuilding = false;
    character.isGoingToBuilding = false;
    character.isSearchingBuilding = false;
    character.targetBuilding = null;
  }

  /**
   * 更新室内角色随机移动
   * @param {Object} character 角色对象
   * @param {number} delta 时间增量（秒）
   * @param {number} gameSpeed 游戏速度倍率
   */
  updateIndoorRandomMovement(character, delta, gameSpeed) {
    // 检查角色是否被鼠标悬停暂停
    if (character.isPausedByHover) {
      return;
    }

    // console.log('updateIndoorRandomMovement', character, delta, gameSpeed);
    // 如果角色在室内但没有停留时间，重置停留时间
    if (character.indoorStayTime === undefined) {
      if (character.id.includes("indoor")) {
        // console.log(`角色${character.id}是室内角色，不设置室内停留时间`);
      } else {
        // console.log(`角色${character.id}未找到室内停留时间，且不是室内角色，重置停留时间`);
        character.indoorStayTime = 10 + Math.random() * 10;
        character.buildingStayTime = 0;
      }
    }

    // 递增室内停留时间计数器
    character.buildingStayTime += delta * gameSpeed;

    // 如果超过停留时间，让角色离开建筑物
    if (character.buildingStayTime >= character.indoorStayTime && !character.isWorking) {
      // console.log(`角色${character.id}在建筑物内停留时间到达上限，准备离开`, character.indoorStayTime, character.buildingStayTime);
      this.exitBuilding(character);
      return;
    }

    // 如果角色正在工作，不离开建筑，仅记录日志
    if (character.buildingStayTime >= character.indoorStayTime && character.isWorking) {
      // 重置停留时间计时器，但不离开建筑
      character.buildingStayTime = 0;
      character.indoorStayTime = 30 + Math.random() * 30; // 更新新的停留时间
      // console.log(`角色${character.id}正在工作中，延长室内停留时间`);
      return;
    }

    // 确保有角色精灵
    if (!character.sprite) {
      // console.warn('角色没有有效的sprite对象，无法更新室内移动');
      return;
    }

    this.moveRandomInRoom(character);
  }

  /**
   * 让角色离开建筑
   * @param {Object} character 角色对象
   * @returns {boolean} 是否成功离开
   */
  exitBuilding(character) {
    // console.log(`角色${character.id}尝试离开建筑物...`, character);

    // 检查角色是否在室内
    if (!character.isIndoor || !character.currentBuilding) {
      console.warn(`角色${character.id}不在室内，无法执行离开操作`);
      return false;
    }

    // 获取当前建筑物
    const building = character.currentBuilding;

    // 获取当前房间和楼层
    const currentRoom = character.currentRoom;

    // 检查角色精灵是否存在
    if (!character.sprite) {
      console.warn(`角色${character.id}没有有效的sprite对象，无法离开建筑`);
      return false;
    }

    // 从房间容器中移除角色精灵
    if (currentRoom && character.sprite.parent === currentRoom) {
      currentRoom.removeChild(character.sprite);
      // console.log(`已从${building.buildingId}房间容器中移除角色${character.id}的精灵`, currentRoom, character);
    }

    // 从室内角色数组中移除该角色
    if (currentRoom && currentRoom.indoorCharacters) {
      try {
        // 获取要删除的角色ID
        const characterIdToRemove = character.id || character.characterId;

        // 查找匹配ID的角色索引
        const index = currentRoom.indoorCharacters.findIndex(indoorChar => {
          const indoorCharId = indoorChar.id || indoorChar.characterId ||
            (indoorChar.sprite && (indoorChar.sprite.characterId || indoorChar.sprite.id));
          return indoorCharId === characterIdToRemove;
        });

        // 如果找到角色，则删除
        if (index > -1) {
          currentRoom.indoorCharacters.splice(index, 1);
          // console.log(`已从${building.buildingId}房间容器列表中移除角色ID=${characterIdToRemove}`);

          // 更新室外人物计数
          const gameStore = useGameStore();
          gameStore.populationOutdoor = (gameStore.populationOutdoor || 0) + 1;
          // console.log(`角色${character.id}离开建筑，室外人物总数增加为: ${gameStore.populationOutdoor}`);
        }
      } catch (error) {
        console.error(`移除室内角色时出错:`, error);
      }
    }

    // 计算建筑物出口位置
    const exitPoint = {
      x: building.x + building.width / 2,
      y: building.y + building.height + (character.sprite.height / 2)
    };

    // 如果有自定义出口点，使用它
    if (building.exitPoint) {
      exitPoint.x = building.exitPoint.x;
      exitPoint.y = building.exitPoint.y;
    }

    // console.log(`建筑物出口位置: (${exitPoint.x}, ${exitPoint.y})`);

    // 重置角色的室内状态
    character.sprite.isIndoor = false;
    character.isIndoor = false;
    character.currentBuilding = null;
    character.currentFloor = null;
    character.currentRoom = null;
    character.indoorStayTime = undefined;
    character.buildingStayTime = undefined;
    character.indoorMovementTimer = undefined;
    character.bounds = null;

    // 设置角色位置到出口
    character.sprite.x = exitPoint.x;
    character.sprite.y = exitPoint.y;
    character.x = exitPoint.x;
    character.y = exitPoint.y;
    character.sprite.zIndex = building.y;
    // console.log('添加到户外场景character.sprite.zIndex', building);
    // 确保精灵可见
    character.sprite.visible = true;
    // 如果游戏对象存在cityMap，将角色添加回户外场景
    const gameStore = useGameStore();
    const sceneLayer = gameStore.pixiApp?.stage?.children[0]?.children[3];
    // console.log('sceneLayer', sceneLayer);
    if (sceneLayer) {
      sceneLayer.addChild(character.sprite);
      // console.log(`已将角色${character.id}添加到户外场景`, character);
    } else {
      console.warn('未找到户外场景容器，无法添加角色');
    }
    
    // 检查当前房间是否正在被hover查看，如果是则不要隐藏房间
    // 通过检查房间是否可见以及其父元素是否有isBeingHovered属性来判断
    const isRoomBeingHovered = currentRoom && currentRoom.visible && 
                              currentRoom.parent && currentRoom.parent.isBeingHovered;
    
    // 只有在房间没有被hover查看时才隐藏
    if (!isRoomBeingHovered) {
      currentRoom.visible = false;
    }
    
    // console.log(`角色${character.id}已成功离开建筑物`);
    return true;
  }

  /**
   * 检查是否存在碰撞，并返回新的可行位置
   * @param {number} x 目标x坐标
   * @param {number} y 目标y坐标
   * @param {string} characterId 当前角色ID
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Object} 安全的位置坐标
   */
  checkAndResolveCollisions(x, y, characterId, tileWidth, tileHeight) {
    // 计算网格坐标
    const gridX = Math.floor(x / tileWidth);
    const gridY = Math.floor(y / tileHeight);

    // 检查该位置是否有其他角色
    const positionKey = `${gridX},${gridY}`;
    if (this.characterPositions.has(positionKey) &&
      this.characterPositions.get(positionKey).id !== characterId) {

      // 计算轻微偏移，避免完全重叠
      const offsetX = (Math.random() * 2 - 1) * (tileWidth * 0.3);
      const offsetY = (Math.random() * 2 - 1) * (tileHeight * 0.3);

      return {
        x: x + offsetX,
        y: y + offsetY
      };
    }

    // 无碰撞，返回原始位置
    return { x, y };
  }

  /**
   * 判断指定位置是否为装饰物区域
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为装饰物区域
   */
  isOnDecoration(gridX, gridY) {
    // 检查是否有全局装饰物数据
    if (!window.decorationTiles) {
      return false;
    }

    // 检查位置是否在装饰物列表中
    return window.decorationTiles.has(`${gridX},${gridY}`);
  }

  /**
   * 清理路径缓存
   */
  clearPathCache() {
    this.pathCache.clear();
  }

  /**
   * 移动角色到目标位置
   * @param {Object} character 角色对象
   * @param {number} deltaTime 时间增量
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  moveCharacterToTarget(character, deltaTime, tileWidth, tileHeight) {
    // 检查角色是否被鼠标悬停暂停
    if (character.isPausedByHover) {
      return;
    }

    // 计算当前位置到目标位置的向量
    const dx = character.targetX - character.sprite.x;
    const dy = character.targetY - character.sprite.y;

    // 计算向量长度
    const distance = Math.sqrt(dx * dx + dy * dy);

    // 获取游戏速度
    const gameStore = useGameStore();
    const speedMultiplier = gameStore.gameSpeed;

    // 如果到达目标位置或非常接近
    const speedThreshold = Math.max(2, speedMultiplier * 2);
    if (distance < speedThreshold) {
      // 检查是否有路径点需要继续移动
      if (character.pathPoints && character.pathPoints.length > 0) {
        // 移动到下一个路径点
        const nextPoint = character.pathPoints.shift();
        character.targetX = nextPoint.x;
        character.targetY = nextPoint.y;
      } else {
        // 已经到达最终目标
        character.sprite.x = character.targetX;
        character.sprite.y = character.targetY;
        character.x = character.targetX;
        character.y = character.targetY;
        character.isMoving = false;

        // 停止动画
        if (character.animatedSprite && character.animatedSprite.playing) {
          character.animatedSprite.stop();
          character.animatedSprite.gotoAndStop(0); // 回到第一帧
        }

        // 更新zIndex
        character.sprite.zIndex = character.y;

        // 室外人物特殊处理：更新网格位置，检查是否到达建筑
        if (!character.isIndoor) {
          character.gridX = Math.floor(character.x / tileWidth);
          character.gridY = Math.floor(character.y / tileHeight);

          // 如果正在前往建筑，且已到达建筑门口
          if (character.isGoingToBuilding && character.targetBuilding) {
            this.enterBuilding(character, character.targetBuilding, tileWidth, tileHeight);
          }
        }
      }
    } else {
      // 计算规范化的方向向量
      const nx = dx / distance;
      const ny = dy / distance;

      // 根据移动方向决定角色面向
      if (character.sprite) {
        if (nx < 0 && character.sprite.scale.x < 0) {
          // 向左移动时翻转精灵
          character.sprite.scale.x = 1;
        } else if (nx > 0 && character.sprite.scale.x > 0) {
          // 向右移动时翻转精灵
          character.sprite.scale.x = -1;
        }
      }

      // 移动精灵，并应用游戏速度倍率
      const movementSpeed = character.speed * speedMultiplier;

      // 优化：限制单帧最大移动距离，防止高速时跳动过大
      const maxFrameDistance = Math.min(distance, movementSpeed);
      character.sprite.x += nx * maxFrameDistance;
      character.sprite.y += ny * maxFrameDistance;

      // 更新人物坐标
      character.x = character.sprite.x;
      character.y = character.sprite.y;

      // 室外人物特殊处理：更新网格坐标
      if (!character.isIndoor) {
        character.gridX = Math.floor(character.x / tileWidth);
        character.gridY = Math.floor(character.y / tileHeight);
      }

      // 更新zIndex确保远处人物被近处人物遮挡
      character.sprite.zIndex = character.y;
    }
  }

  /**
   * 人物工作移动
   * @param {Object} character 人物数据
   * @param {number} elapsedTime 经过的时间（秒）
   * @returns {boolean} 是否已到达目标位置
   */
  moveToWork(character, elapsedTime) {
    // 获取游戏配置参数
    const tileWidth = 128;  // 保证瓦片宽度始终为固定值
    const tileHeight = 128; // 保证瓦片高度始终为固定值

    // 检查目标坐标的有效性
    if (isNaN(character.targetX) || isNaN(character.targetY) ||
      !isFinite(character.targetX) || !isFinite(character.targetY) ||
      character.targetX === undefined || character.targetY === undefined) {
      console.warn(`检测到角色(${character.id || 'unknown'})的无效目标坐标: x=${character.targetX}, y=${character.targetY}`);
      // 重置到当前位置
      character.targetX = character.x;
      character.targetY = character.y;
      character.isMoving = false;
      return true; // 视为已到达，阻止继续移动
    }

    // 检查坐标是否过大（可能是错误导致的）
    if (Math.abs(character.targetX) > 10000 || Math.abs(character.targetY) > 10000) {
      console.warn(`检测到角色(${character.id || 'unknown'})的目标坐标异常大: x=${character.targetX}, y=${character.targetY}，已重置`);
      // 重置到当前位置
      character.targetX = character.x;
      character.targetY = character.y;
      character.isMoving = false;
      return true; // 视为已到达，阻止继续移动
    }

    // 检查是否需要重新计算路径（来自EventModalProcess的标记）
    if (character.needsPathfinding) {
      character.needsPathfinding = false; // 重置标记

      // 清空旧路径点
      character.pathPoints = [];

      // 设置路径点
      this.calculateCharacterPath(character, tileWidth, tileHeight);
    }

    // 检查角色是否已经到达目标位置
    const dx = character.targetX - character.x;
    const dy = character.targetY - character.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    // 如果距离非常近，认为已到达
    if (distance < 15) {
      // 如果有最终目标坐标，切换到最终目标
      if (character.finalTargetX !== undefined && character.finalTargetY !== undefined) {
        // 检查最终目标坐标是否有效
        if (isNaN(character.finalTargetX) || isNaN(character.finalTargetY) ||
          !isFinite(character.finalTargetX) || !isFinite(character.finalTargetY) ||
          Math.abs(character.finalTargetX) > 10000 || Math.abs(character.finalTargetY) > 10000) {
          console.warn(`检测到角色(${character.id || 'unknown'})的无效最终目标坐标，已忽略`);
          delete character.finalTargetX;
          delete character.finalTargetY;
          return true; // 视为已到达
        }

        character.targetX = character.finalTargetX;
        character.targetY = character.finalTargetY;
        // 清除最终目标标记，避免循环
        delete character.finalTargetX;
        delete character.finalTargetY;
        return false; // 还没到达最终目标
      }
      // 如果还有路径点，继续移动到下一个路径点
      else if (character.pathPoints && character.pathPoints.length > 0) {
        const nextPoint = character.pathPoints.shift();

        // 验证下一个路径点的有效性
        if (!nextPoint || isNaN(nextPoint.x) || isNaN(nextPoint.y) ||
          !isFinite(nextPoint.x) || !isFinite(nextPoint.y) ||
          Math.abs(nextPoint.x) > 10000 || Math.abs(nextPoint.y) > 10000) {
          console.warn(`检测到角色(${character.id || 'unknown'})的无效路径点，已忽略剩余路径`);
          character.pathPoints = []; // 清空剩余的路径点
          character.isMoving = false;
          return true; // 视为已到达
        }

        character.targetX = nextPoint.x;
        character.targetY = nextPoint.y;
        character.isMoving = true;
        return false; // 还没到达最终目标
      } else {
        // 到达最终目标
        character.isMoving = false;
        if (character.isWorking !== 0) {
          character.animatedSprite.stop();
          character.animatedSprite.gotoAndStop(0); // 回到第一帧
        }
        return true; // 已到达目标
      }
    }

    // 如果角色还没有开始移动，需要设置移动状态
    if (!character.isMoving) {
      // 计算路径
      this.calculateCharacterPath(character, tileWidth, tileHeight);

      // 设置移动状态
      character.isMoving = true;

      // 设置角色朝向
      if (character.sprite) {
        if (dx < 0) {
          // 向左移动
          character.sprite.scale.x = 1;
        } else {
          // 向右移动
          character.sprite.scale.x = -1;
        }
      }

      // 开始播放动画
      if (character.animatedSprite && !character.animatedSprite.playing) {
        character.animatedSprite.play();
      }
    }

    return false; // 还没到达最终目标
  }

  /**
   * 计算角色到目标的路径
   * @param {Object} character 角色对象
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  calculateCharacterPath(character, tileWidth, tileHeight) {
    // 验证角色和目标坐标
    if (!character || isNaN(character.x) || isNaN(character.y) ||
      isNaN(character.targetX) || isNaN(character.targetY)) {
      console.warn('路径计算失败：无效的角色或坐标');
      return;
    }

    // 检查坐标是否异常大
    if (Math.abs(character.x) > 10000 || Math.abs(character.y) > 10000 ||
      Math.abs(character.targetX) > 10000 || Math.abs(character.targetY) > 10000) {
      console.warn(`路径计算失败：坐标值异常大 (${character.x},${character.y}) -> (${character.targetX},${character.targetY})`);
      return;
    }

    // 检查从当前位置到目标位置的路径是否有障碍物
    const startGridX = Math.floor(character.x / tileWidth);
    const startGridY = Math.floor(character.y / tileHeight);
    const endGridX = Math.floor(character.targetX / tileWidth);
    const endGridY = Math.floor(character.targetY / tileHeight);

    // 验证网格坐标的合法性
    if (isNaN(startGridX) || isNaN(startGridY) || isNaN(endGridX) || isNaN(endGridY)) {
      console.warn(`路径计算失败：无效的网格坐标 (${startGridX},${startGridY}) -> (${endGridX},${endGridY})`);
      return;
    }

    // 检查是否有建筑物阻挡
    if (this.hasObstacleInPath(startGridX, startGridY, endGridX, endGridY)) {
      // 计算避开障碍物的路径
      const pathPoints = this.findPath(
        startGridX, startGridY,
        endGridX, endGridY,
        tileWidth, tileHeight
      );

      if (pathPoints && pathPoints.length > 0) {
        // 验证路径点的有效性
        const validPathPoints = pathPoints.filter(point => {
          if (!point || isNaN(point.x) || isNaN(point.y) ||
            !isFinite(point.x) || !isFinite(point.y) ||
            Math.abs(point.x) > 10000 || Math.abs(point.y) > 10000) {
            console.warn(`发现无效的路径点 (${point?.x},${point?.y})，已忽略`);
            return false;
          }
          return true;
        });

        // 设置路径点
        character.pathPoints = validPathPoints;

        // 如果有有效路径点，设置第一个路径点作为临时目标
        if (character.pathPoints.length > 0) {
          const firstPoint = character.pathPoints.shift();
          character.targetX = firstPoint.x;
          character.targetY = firstPoint.y;
        } else {
          // 没有有效路径点，尝试使用简单绕行
          this.setSimpleDetourPath(character, startGridX, startGridY, endGridX, endGridY, tileWidth, tileHeight);
        }
      } else {
        // 无法找到路径，尝试使用简单绕行
        this.setSimpleDetourPath(character, startGridX, startGridY, endGridX, endGridY, tileWidth, tileHeight);
      }
    }
  }

  /**
   * 设置简单绕行路径
   * @param {Object} character 角色对象
   * @param {number} startX 起点X
   * @param {number} startY 起点Y
   * @param {number} endX 终点X
   * @param {number} endY 终点Y
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   */
  setSimpleDetourPath(character, startX, startY, endX, endY, tileWidth, tileHeight) {
    // 尝试围绕建筑物的简单绕行
    const directions = [
      { dx: 0, dy: 1 },  // 下
      { dx: 1, dy: 0 },  // 右
      { dx: -1, dy: 0 }, // 左
      { dx: 0, dy: -1 }, // 上
      { dx: 1, dy: 1 },  // 右下
      { dx: -1, dy: 1 }, // 左下
      { dx: 1, dy: -1 }, // 右上
      { dx: -1, dy: -1 } // 左上
    ];

    // 找到一个没有障碍物的临时中间点
    let foundSafePath = false;
    for (let distance = 1; distance <= 3; distance++) {
      for (const dir of directions) {
        const tempGridX = startX + dir.dx * distance;
        const tempGridY = startY + dir.dy * distance;

        // 检查这个中间点是否有障碍物
        if (!this.isObstacle(tempGridX, tempGridY)) {
          // 设置临时目标点
          character.targetX = tempGridX * tileWidth + tileWidth / 2;
          character.targetY = tempGridY * tileHeight + tileHeight / 2;

          // 保存最终目标为下一个目标
          character.finalTargetX = endX * tileWidth + tileWidth / 2;
          character.finalTargetY = endY * tileHeight + tileHeight / 2;

          foundSafePath = true;
          break;
        }
      }

      if (foundSafePath) break;
    }

    // 如果所有方向都有障碍，直接设置目标点
    if (!foundSafePath) {
      // console.log(`角色${character.id}无法找到安全路径，将直接移动到目标位置: (${endX}, ${endY})`);
      // 直接设置最终目标位置
      character.targetX = endX * tileWidth + tileWidth / 2;
      character.targetY = endY * tileHeight + tileHeight / 2;
    } else {
      // console.log(`角色${character.id}找到最近的道路点: (${character.finalTargetX}, ${character.finalTargetY})`);
    }
  }

  /**
   * 检查从起点到终点的直线路径上是否有建筑物阻挡
   * @param {number} startX 起点X网格坐标
   * @param {number} startY 起点Y网格坐标
   * @param {number} endX 终点X网格坐标
   * @param {number} endY 终点Y网格坐标
   * @returns {boolean} 是否有阻挡
   */
  hasObstacleInPath(startX, startY, endX, endY) {
    // 使用Bresenham算法检查直线路径上的每个网格
    const points = this.getLinePoints(startX, startY, endX, endY);

    // 检查每个点是否是建筑物
    for (const point of points) {
      if (this.isObstacle(point.x, point.y)) {
        return true;
      }
    }

    return false;
  }

  /**
   * 使用Bresenham算法获取两点之间的所有网格点
   * @param {number} x0 起点X
   * @param {number} y0 起点Y
   * @param {number} x1 终点X
   * @param {number} y1 终点Y
   * @returns {Array} 路径上的所有网格点
   */
  getLinePoints(x0, y0, x1, y1) {
    const points = [];
    const dx = Math.abs(x1 - x0);
    const dy = Math.abs(y1 - y0);
    const sx = (x0 < x1) ? 1 : -1;
    const sy = (y0 < y1) ? 1 : -1;
    let err = dx - dy;

    let x = x0;
    let y = y0;

    // 避免包含起点和终点
    if (x === x1 && y === y1) return points;

    while (true) {
      // 只添加不是起点和终点的点
      if (!(x === x0 && y === y0) && !(x === x1 && y === y1)) {
        points.push({ x, y });
      }

      if (x === x1 && y === y1) break;

      const e2 = 2 * err;
      if (e2 > -dy) {
        err -= dy;
        x += sx;
      }
      if (e2 < dx) {
        err += dx;
        y += sy;
      }
    }

    return points;
  }

  /**
   * 检查指定网格位置是否为障碍物
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为障碍物
   */
  isObstacle(gridX, gridY) {
    // 获取游戏状态store
    const gameStore = useGameStore();
    
    // 检查是否有建筑物
    const gridKey = `${gridX},${gridY}`;
    if (gameStore.buildingData && gameStore.buildingData.has(gridKey)) {
      return true;
    }

    // 检查是否是装饰物
    if (this.isOnDecoration(gridX, gridY)) {
      return true;
    }

    return false;
  }

  /**
   * 使用A*算法寻找从起点到终点的最短路径
   * @param {number} startX 起点X网格坐标
   * @param {number} startY 起点Y网格坐标
   * @param {number} endX 终点X网格坐标
   * @param {number} endY 终点Y网格坐标
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array} 路径点数组，每个点包含{x,y}像素坐标
   */
  findPath(startX, startY, endX, endY, tileWidth, tileHeight) {
    // 生成缓存键
    const cacheKey = `${startX},${startY}_${endX},${endY}`;

    // 检查缓存
    if (this.pathCache.has(cacheKey)) {
      return [...this.pathCache.get(cacheKey)]; // 返回缓存路径的拷贝
    }
    
    // 简化版A*算法
    const openSet = [];
    const closedSet = new Set();
    const cameFrom = new Map();

    // 距离
    const gScore = new Map();
    const fScore = new Map();

    // 初始化起点
    const startKey = `${startX},${startY}`;
    gScore.set(startKey, 0);
    // 使用曼哈顿距离替代原来的启发式函数
    const manhattanDistance = Math.abs(endX - startX) + Math.abs(endY - startY);
    fScore.set(startKey, manhattanDistance);
    
    openSet.push({
      x: startX,
      y: startY,
      f: fScore.get(startKey)
    });

    // 设置最大迭代次数，防止无限循环
    const maxIterations = 2000;
    let iterations = 0;

    while (openSet.length > 0 && iterations < maxIterations) {
      iterations++;

      // 排序找出F值最小的节点
      openSet.sort((a, b) => a.f - b.f);
      const current = openSet.shift();
      const currentKey = `${current.x},${current.y}`;

      // 如果到达终点
      if (current.x === endX && current.y === endY) {
        // 构建路径
        const path = [];
        let currentNode = current;

        while (true) {
          const key = `${currentNode.x},${currentNode.y}`;
          // 转换为像素坐标
          path.unshift({
            x: currentNode.x * tileWidth + tileWidth / 2,
            y: currentNode.y * tileHeight + tileHeight / 2
          });

          if (!cameFrom.has(key)) break;
          currentNode = cameFrom.get(key);
        }

        // 移除第一个点（起点）
        if (path.length > 0) {
          path.shift();
        }

        // 缓存路径
        this.pathCache.set(cacheKey, [...path]);
        return path;
      }

      closedSet.add(currentKey);

      // 获取相邻节点（8个方向）
      // 八个方向：上、下、左、右、左上、右上、左下、右下
      const directions = [
        { x: 0, y: -1 },  // 上
        { x: 0, y: 1 },   // 下
        { x: -1, y: 0 },  // 左
        { x: 1, y: 0 },   // 右
        { x: -1, y: -1 }, // 左上
        { x: 1, y: -1 },  // 右上
        { x: -1, y: 1 },  // 左下
        { x: 1, y: 1 }    // 右下
      ];

      for (const dir of directions) {
        const nx = current.x + dir.x;
        const ny = current.y + dir.y;
        const neighborKey = `${nx},${ny}`;

        // 跳过已处理过的节点
        if (closedSet.has(neighborKey)) {
          continue;
        }

        // 检查是否是障碍物
        if (this.isObstacle(nx, ny)) {
          continue;
        }

        // 设置移动成本
        const isDiagonal = dir.x !== 0 && dir.y !== 0;
        const moveCost = isDiagonal ? 1.414 : 1; // 对角线移动成本为1.414

        // 计算从起点经过当前节点到邻居节点的距离
        const tentativeGScore = gScore.get(currentKey) + moveCost;

        // 检查是否已经有更好的路径
        if (!gScore.has(neighborKey) || tentativeGScore < gScore.get(neighborKey)) {
          // 更新来源和分数
          cameFrom.set(neighborKey, current);
          gScore.set(neighborKey, tentativeGScore);
          // 曼哈顿距离作为启发式
          const h = Math.abs(nx - endX) + Math.abs(ny - endY);
          fScore.set(neighborKey, tentativeGScore + h);

          // 检查邻居是否已在开放集合中
          const inOpenSet = openSet.some(node => node.x === nx && node.y === ny);

          if (!inOpenSet) {
            openSet.push({
              x: nx,
              y: ny,
              f: fScore.get(neighborKey)
            });
          }
        }
      }
    }

    // 如果没有找到路径，创建一个直接到目标点的简单路径
    console.warn(`从(${startX},${startY})到(${endX},${endY})的路径查找失败，创建直线路径`);
    const directPath = [{
      x: endX * tileWidth + tileWidth / 2,
      y: endY * tileHeight + tileHeight / 2
    }];

    // 缓存这个直接路径
    this.pathCache.set(cacheKey, [...directPath]);
    return directPath;
  }

  /**
   * 通过中间路径点尝试找到一条到目标的路径
   * @param {number} startX 起点X坐标
   * @param {number} startY 起点Y坐标
   * @param {number} endX 终点X坐标
   * @param {number} endY 终点Y坐标
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array|null} 找到的路径点数组，如果失败则返回null
   */
  findPathThroughWaypoints(startX, startY, endX, endY, tileWidth, tileHeight) {
    // 计算起点和终点之间的曼哈顿距离
    const distance = Math.abs(endX - startX) + Math.abs(endY - startY);
    
    // 如果距离很小，不需要使用中间点
    if (distance <= 5) return null;
    
    // 确定方向
    const dx = endX - startX;
    const dy = endY - startY;
    
    // 定义可能的中间点
    const waypoints = [];
    
    // 偏好水平方向移动
    if (Math.abs(dx) > Math.abs(dy)) {
      // 添加几个可能的中间点：先水平移动
      waypoints.push({
        x: startX + Math.sign(dx) * Math.floor(Math.abs(dx) * 0.5),
        y: startY
      });
      
      // 另一个中间点：水平移动到终点X坐标，保持起点Y坐标
      waypoints.push({
        x: endX,
        y: startY
      });
    } else {
      // 添加几个可能的中间点：先保持X坐标不变，垂直移动
      waypoints.push({
        x: startX,
        y: startY + Math.sign(dy) * Math.floor(Math.abs(dy) * 0.5)
      });
      
      // 另一个中间点：垂直移动到终点Y坐标，保持起点X坐标
      waypoints.push({
        x: startX,
        y: endY
      });
    }
    
    // 再添加一些其他可能的中间点
    waypoints.push({
      x: startX + Math.sign(dx) * Math.floor(Math.abs(dx) * 0.7),
      y: startY + Math.sign(dy) * Math.floor(Math.abs(dy) * 0.3)
    });
    
    waypoints.push({
      x: startX + Math.sign(dx) * Math.floor(Math.abs(dx) * 0.3),
      y: startY + Math.sign(dy) * Math.floor(Math.abs(dy) * 0.7)
    });
    
    // 过滤掉是障碍物的中间点
    const validWaypoints = waypoints.filter(wp => !this.isObstacle(wp.x, wp.y));
    
    // 如果没有有效的中间点，返回null
    if (validWaypoints.length === 0) return null;
    
    // 尝试通过每个中间点寻找路径
    for (const waypoint of validWaypoints) {
      // 寻找从起点到中间点的路径（使用简单的直接路径算法，避免递归）
      const pathToWaypoint = this.findSimplePathTowards(
        startX, startY, waypoint.x, waypoint.y, tileWidth, tileHeight
      );
      
      // 如果找不到到中间点的路径，尝试下一个中间点
      if (!pathToWaypoint || pathToWaypoint.length === 0) continue;
      
      // 寻找从中间点到终点的路径
      const pathFromWaypointToEnd = this.findSimplePathTowards(
        waypoint.x, waypoint.y, endX, endY, tileWidth, tileHeight
      );
      
      // 如果找不到从中间点到终点的路径，尝试下一个中间点
      if (!pathFromWaypointToEnd || pathFromWaypointToEnd.length === 0) continue;
      
      // 如果我们找到了一个完整的路径（起点->中间点->终点），返回合并的路径
      return [...pathToWaypoint, ...pathFromWaypointToEnd];
    }
    
    // 如果所有中间点都不成功，返回null
    return null;
  }
  
  /**
   * 使用简化的路径查找算法，寻找朝向目标的路径
   * 这个方法避免了完整的A*，适用于创建局部路径
   * @param {number} startX 起点X坐标
   * @param {number} startY 起点Y坐标
   * @param {number} endX 终点X坐标
   * @param {number} endY 终点Y坐标
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array} 找到的路径点数组
   */
  findSimplePathTowards(startX, startY, endX, endY, tileWidth, tileHeight) {
    // 使用贪婪算法找到一条简单路径
    const path = [];
    let currentX = startX;
    let currentY = startY;
    
    // 最大步数限制，防止无限循环
    const maxSteps = 20;
    let steps = 0;
    
    while ((currentX !== endX || currentY !== endY) && steps < maxSteps) {
      steps++;
      
      // 确定下一步的最佳方向
      const dx = Math.sign(endX - currentX);
      const dy = Math.sign(endY - currentY);
      
      // 优先尝试的移动顺序：先单独x或y方向，再对角线
      const moves = [];
      
      // 如果x方向有差距，添加水平移动
      if (dx !== 0) {
        moves.push({ x: currentX + dx, y: currentY, isDiagonal: false });
      }
      
      // 如果y方向有差距，添加垂直移动
      if (dy !== 0) {
        moves.push({ x: currentX, y: currentY + dy, isDiagonal: false });
      }
      
      // 如果x和y方向都有差距，添加对角线移动
      if (dx !== 0 && dy !== 0) {
        moves.push({ x: currentX + dx, y: currentY + dy, isDiagonal: true });
      }
      
      // 查找第一个不是障碍物的移动
      let moved = false;
      for (const move of moves) {
        // 对于对角线移动，需要检查两个相邻格子是否都不是障碍物
        if (move.isDiagonal) {
          if (!this.isObstacle(move.x, move.y) && 
              !this.isObstacle(currentX + dx, currentY) && 
              !this.isObstacle(currentX, currentY + dy)) {
            currentX = move.x;
            currentY = move.y;
            moved = true;
            break;
          }
        } else {
          if (!this.isObstacle(move.x, move.y)) {
            currentX = move.x;
            currentY = move.y;
            moved = true;
            break;
          }
        }
      }
      
      // 如果找不到可行的移动，寻路失败
      if (!moved) {
        break;
      }
      
      // 添加到路径中
      path.push({
        x: currentX * tileWidth + tileWidth / 2,
        y: currentY * tileHeight + tileHeight / 2
      });
      
      // 如果到达目标点，结束寻路
      if (currentX === endX && currentY === endY) {
        break;
      }
    }
    
    return path;
  }
  
  /**
   * 创建一条可行的路径，即使不能直接到达目标
   * 这是一种备选策略，当其他路径查找方法失败时使用
   * @param {number} startX 起点X坐标
   * @param {number} startY 起点Y坐标
   * @param {number} endX 终点X坐标
   * @param {number} endY 终点Y坐标
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array} 创建的路径点数组
   */
  createViablePath(startX, startY, endX, endY, tileWidth, tileHeight) {
    // 获取从起点出发的所有可行方向
    const gameStore = useGameStore();
    const directions = [
      { dx: 1, dy: 0, name: "右" },
      { dx: -1, dy: 0, name: "左" },
      { dx: 0, dy: -1, name: "上" },
      { dx: 0, dy: 1, name: "下" },
      { dx: 1, dy: -1, name: "右上" },
      { dx: -1, dy: -1, name: "左上" },
      { dx: 1, dy: 1, name: "右下" },
      { dx: -1, dy: 1, name: "左下" }
    ];
    
    // 计算每个方向的评分（基于到目标的距离）
    const scoredDirections = directions
      .filter(dir => !this.isObstacle(startX + dir.dx, startY + dir.dy))
      .map(dir => {
        const newX = startX + dir.dx;
        const newY = startY + dir.dy;
        const distToTarget = Math.abs(endX - newX) + Math.abs(endY - newY);
        
        // 优先选择水平和垂直方向
        const directionScore = dir.dx !== 0 && dir.dy !== 0 ? 2 : 1;
        
        // 总分（越低越好）
        const score = distToTarget * directionScore;
        
        return { 
          dx: dir.dx, 
          dy: dir.dy, 
          name: dir.name,
          score,
          newX,
          newY
        };
      });
    
    // 如果没有可行方向，返回空路径
    if (scoredDirections.length === 0) {
      return [];
    }
    
    // 按评分排序
    scoredDirections.sort((a, b) => a.score - b.score);
    
    // 选择评分最低的方向，创建一个简单路径
    const bestDirection = scoredDirections[0];
    // console.log(`选择最优方向：${bestDirection.name}，得分：${bestDirection.score}`);
    
    // 创建一个路径点
    return [{
      x: bestDirection.newX * tileWidth + tileWidth / 2,
      y: bestDirection.newY * tileHeight + tileHeight / 2
    }];
  }

  /**
   * 启发式函数：曼哈顿距离
   * @param {number} x1 起点X
   * @param {number} y1 起点Y
   * @param {number} x2 终点X
   * @param {number} y2 终点Y
   * @returns {number} 估计距离
   */
  heuristic(x1, y1, x2, y2) {
    return Math.abs(x1 - x2) + Math.abs(y1 - y2);
  }

  /**
   * 获取指定位置的相邻节点
   * @param {number} x 当前X坐标
   * @param {number} y 当前Y坐标
   * @returns {Array} 相邻节点数组
   */
  getNeighbors(x, y) {
    const neighbors = [];
    
    // 记录已经添加的方向，用于调试
    const addedDirections = [];

    // 八个方向：上、下、左、右、左上、右上、左下、右下
    const directions = [
      { x: 0, y: -1, name: "上" }, // 上
      { x: 0, y: 1, name: "下" },  // 下
      { x: -1, y: 0, name: "左" }, // 左
      { x: 1, y: 0, name: "右" },  // 右
      { x: -1, y: -1, name: "左上" }, // 左上
      { x: 1, y: -1, name: "右上" },  // 右上
      { x: -1, y: 1, name: "左下" },  // 左下
      { x: 1, y: 1, name: "右下" }    // 右下
    ];

    // 首先添加四个基本方向（上下左右）
    for (let i = 0; i < 4; i++) {
      const dir = directions[i];
      const nx = x + dir.x;
      const ny = y + dir.y;

      // 检查新位置是否不是障碍物
      if (!this.isObstacle(nx, ny)) {
        neighbors.push({
          x: nx,
          y: ny,
          isDiagonal: false,
          direction: dir.name,
          cost: 1 // 直线移动的标准成本
        });
        addedDirections.push(dir.name);
      }
    }

    // 然后检查对角线方向，允许沿着建筑物边缘移动
    for (let i = 4; i < 8; i++) {
      const dir = directions[i];
      const nx = x + dir.x;
      const ny = y + dir.y;
      
      // 对于对角线移动，检查目标点是否不是障碍物
      if (!this.isObstacle(nx, ny)) {
        // 检查相邻的两个直线方向是否至少有一个是可行的
        // 例如：对于左上((-1,-1))，检查左(-1,0)和上(0,-1)
        const adjacentDir1 = { x: dir.x, y: 0 }; // 水平相邻
        const adjacentDir2 = { x: 0, y: dir.y }; // 垂直相邻
        
        const horizontalFree = !this.isObstacle(x + adjacentDir1.x, y + adjacentDir1.y);
        const verticalFree = !this.isObstacle(x + adjacentDir2.x, y + adjacentDir2.y);
        
        // 只要水平或垂直方向至少有一个是自由的，就允许对角线移动
        // 这样就可以沿着建筑物边缘移动
        if (horizontalFree || verticalFree) {
          let edgeCost = 1.414; // 标准对角线成本（根号2）
          
          // 如果是沿边缘移动（只有一个方向是自由的），成本稍高
          if (!(horizontalFree && verticalFree)) {
            edgeCost = 1.7; // 增加沿边缘移动的成本，使其不太优先
          }
          
          neighbors.push({
            x: nx,
            y: ny,
            isDiagonal: true,
            direction: dir.name,
            cost: edgeCost,
            // 标记是否是沿边缘移动
            edgePath: !(horizontalFree && verticalFree)
          });
          addedDirections.push(dir.name);
        }
      }
    }

    // 如果无法通过对角线到达上方向，检查是否可以强制添加上方向
    const hasTopDirections = addedDirections.some(dir => ["上", "左上", "右上"].includes(dir));
    
    if (!hasTopDirections) {
      // 尝试找到上方的可能路径
      for (const dir of directions.filter(d => ["上", "左上", "右上"].includes(d.name))) {
        const nx = x + dir.x;
        const ny = y + dir.y;
        
        // 如果目标点不是障碍物，但之前因为边缘检查而被排除
        if (!this.isObstacle(nx, ny) && !addedDirections.includes(dir.name)) {
          // 允许强制添加这个方向，但增加更高的成本
          neighbors.push({
            x: nx,
            y: ny,
            isDiagonal: dir.name !== "上",
            direction: dir.name,
            cost: dir.name === "上" ? 2 : 2.5, // 更高的成本
            forcedPath: true,
            edgePath: true
          });
        }
      }
    }

    return neighbors;
  }

  /**
   * 根据来源信息重建路径
   * @param {Map} cameFrom 节点来源信息
   * @param {Object} current 当前节点
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array} 路径点数组，每个点包含{x,y}像素坐标
   */
  reconstructPath(cameFrom, current, tileWidth, tileHeight) {
    const path = [];
    let currentNode = current;

    while (true) {
      const key = `${currentNode.x},${currentNode.y}`;
      // 转换为像素坐标
      path.unshift({
        x: currentNode.x * tileWidth + tileWidth / 2,
        y: currentNode.y * tileHeight + tileHeight / 2
      });

      if (!cameFrom.has(key)) break;
      currentNode = cameFrom.get(key);
    }

    // 移除第一个点（起点）
    if (path.length > 0) {
      path.shift();
    }

    return path;
  }

  /**
   * 获取可用的方向（考虑视口限制）
   * @param {number} gridX 当前网格X坐标
   * @param {number} gridY 当前网格Y坐标
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @param {number} edgeWidth 边缘宽度
   * @param {Object} currentDirection 当前方向
   * @returns {Array} 可用方向数组
   */
  getAvailableDirectionsInViewport(gridX, gridY, mapWidth, mapHeight, edgeWidth, currentDirection) {
    // 检查视口边界是否设置，如果没有设置，使用原始方法
    if (!this.viewportGridBounds) {
      return this.getAvailableDirections(gridX, gridY, mapWidth, mapHeight, edgeWidth, currentDirection);
    }

    // 四个方向：上、右、下、左
    const directions = [
      { dx: 0, dy: -1, name: 'up' },
      { dx: 1, dy: 0, name: 'right' },
      { dx: 0, dy: 1, name: 'down' },
      { dx: -1, dy: 0, name: 'left' }
    ];

    // 可用方向
    const availableDirections = [];

    // 对向方向映射（用于避免立即掉头）
    const oppositeDirections = {
      up: 'down',
      right: 'left',
      down: 'up',
      left: 'right'
    };

    // 检查每个方向
    for (const dir of directions) {
      // 计算该方向上的下一个格子
      const nx = gridX + dir.dx;
      const ny = gridY + dir.dy;

      // 视口边界检查（留出一定边距）
      if (
        nx < this.viewportGridBounds.left + 1 || 
        nx > this.viewportGridBounds.right - 1 || 
        ny < this.viewportGridBounds.top + 1 || 
        ny > this.viewportGridBounds.bottom - 1
      ) {
        continue;
      }

      // 地图边界检查
      if (nx < 0 || ny < 0 || nx >= mapWidth || ny >= mapHeight) {
        continue;
      }

      // 检查是否是道路
      if (!this.isOnRoad(nx, ny)) {
        continue;
      }

      // 检查该方向是否是当前方向的反方向
      let isOppositeDirection = false;
      if (currentDirection && oppositeDirections[dir.name] === currentDirection.name) {
        isOppositeDirection = true;
      }

      // 为方向设置权重
      let weight = 1;

      // 如果是当前方向，给予更高权重
      if (currentDirection && dir.name === currentDirection.name) {
        weight = 3; // 继续直行的概率更高
      } else if (isOppositeDirection) {
        weight = 0.5; // 掉头的概率更低
      }

      // 添加到可用方向
      availableDirections.push({
        dx: dir.dx,
        dy: dir.dy,
        name: dir.name,
        weight: weight
      });
    }

    return availableDirections;
  }

  /**
   * 在视口内找到下一个十字路口
   * @param {number} gridX 当前网格X坐标
   * @param {number} gridY 当前网格Y坐标
   * @param {Object} direction 移动方向
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @param {number} edgeWidth 边缘宽度
   * @returns {Object|null} 下一个十字路口
   */
  findNextIntersectionInViewport(gridX, gridY, direction, mapWidth, mapHeight, edgeWidth) {
    // 检查视口边界是否设置
    if (!this.viewportGridBounds) {
      return this.findNextIntersection(gridX, gridY, direction, mapWidth, mapHeight, edgeWidth);
    }

    let curX = gridX;
    let curY = gridY;
    let distance = 0;
    const maxDistance = 50; // 最大搜索距离

    // 循环沿着方向移动，直到找到十字路口或离开视口
    while (distance < maxDistance) {
      // 移动到下一个位置
      curX += direction.dx;
      curY += direction.dy;
      distance++;

      // 检查是否离开视口（留出一定边距）
      if (
        curX < this.viewportGridBounds.left + 2 || 
        curX > this.viewportGridBounds.right - 2 || 
        curY < this.viewportGridBounds.top + 2 || 
        curY > this.viewportGridBounds.bottom - 2
      ) {
        // 如果离开视口，返回一个位于视口内的点
        return {
          x: Math.max(this.viewportGridBounds.left + 2, Math.min(curX - direction.dx, this.viewportGridBounds.right - 2)),
          y: Math.max(this.viewportGridBounds.top + 2, Math.min(curY - direction.dy, this.viewportGridBounds.bottom - 2))
        };
      }

      // 检查地图边界
      if (curX < 0 || curY < 0 || curX >= mapWidth || curY >= mapHeight) {
        break;
      }

      // 检查是否是道路
      if (!this.isOnRoad(curX, curY)) {
        break;
      }

      // 检查是否为十字路口
      if (this.isIntersection(curX, curY)) {
        return { x: curX, y: curY };
      }
    }

    // 如果无法找到十字路口，返回视口中心附近的一个点
    if (distance >= maxDistance) {
      const viewportCenterX = Math.floor((this.viewportGridBounds.left + this.viewportGridBounds.right) / 2);
      const viewportCenterY = Math.floor((this.viewportGridBounds.top + this.viewportGridBounds.bottom) / 2);
      
      return { 
        x: viewportCenterX, 
        y: viewportCenterY 
      };
    }

    return null;
  }
}

export default CharacterBehavior; 