/**
 * 人物渲染组件兼容层
 * 用于向后兼容旧版的CharacterRenderer API
 * 实际功能已拆分到CharacterFactory和CharacterBehavior两个类中
 */
import * as PIXI from 'pixi.js';
// 引入游戏状态管理store
import { useGameStore } from '../../stores/gameStore';
// 引入拆分后的人物工厂和行为控制器
import CharacterFactory from './CharacterFactory';
import CharacterBehavior from './CharacterBehavior';

class CharacterRenderer {
  constructor() {
    // 创建人物工厂实例
    this.characterFactory = new CharacterFactory();
    
    // 创建人物行为控制器实例
    this.behaviorController = new CharacterBehavior();
    
    // 获取游戏状态store实例
    this.gameStore = null;

    // 复制工厂类的基本属性，保持API兼容
    this.characterTextures = this.characterFactory.characterTextures;
    this.buildingCharacters = this.characterFactory.buildingCharacters;
    this.characterCounter = this.characterFactory.characterCounter;
    this.characterPositions = new Map();
    this.pathCache = this.behaviorController.pathCache;
  }

  /**
   * 初始化gameStore
   */
  initGameStore() {
    this.gameStore = useGameStore();
    // 同时初始化工厂和行为控制器的gameStore
    this.characterFactory.initGameStore();
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
   * 初始化样式 - 兼容接口，转发到工厂
   */
  initializeStyles() {
    this.characterFactory.initializeStyles();
    this.styles = this.characterFactory.styles;
  }

  /**
   * 获取随机颜色 - 兼容接口，转发到工厂
   * @param {Array} colorOptions 可选颜色数组
   * @returns {number} 随机选择的颜色
   */
  getRandomColor(colorOptions) {
    return this.characterFactory.getRandomColor(colorOptions);
  }

  /**
   * 获取随机人物类型 - 兼容接口，转发到工厂
   * @returns {string} 随机人物类型
   */
  getRandomCharacterType() {
    return this.characterFactory.getRandomCharacterType();
  }

  /**
   * 渲染人物纹理 - 兼容接口，转发到工厂
   * @param {string} characterType 人物类型
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {PIXI.Application} app PIXI应用实例
   * @returns {PIXI.Container} 人物容器
   */
  renderCharacter(characterType, tileWidth, tileHeight, app) {
    return this.characterFactory.renderCharacter(characterType, tileWidth, tileHeight, app);
  }

  /**
   * 为人物创建阴影 - 兼容接口，转发到工厂
   * @param {PIXI.Container} sprite 人物容器
   * @param {boolean} isIndoor 是否为室内人物
   * @returns {PIXI.Sprite} 阴影精灵
   */
  createCharacterShadow(sprite, isIndoor = false) {
    return this.characterFactory.createCharacterShadow(sprite, isIndoor);
  }

  /**
   * 创建人物精灵 - 兼容接口，转发到工厂
   * @param {Object} options 创建选项
   * @returns {PIXI.Sprite} 人物精灵
   */
  createCharacter(options) {
    return this.characterFactory.createCharacter(options);
  }

  /**
   * 创建室外人物精灵 - 兼容接口，转发到工厂
   * @param {Object} options 创建选项
   * @returns {PIXI.Sprite} 人物精灵
   */
  createOutdoorCharacter(options) {
    return this.characterFactory.createOutdoorCharacter(options);
  }

  /**
   * 创建室内人物精灵 - 兼容接口，转发到工厂
   * @param {Object} options 创建选项 
   * @returns {PIXI.Sprite} 人物精灵
   */
  createIndoorCharacter(options) {
    return this.characterFactory.createIndoorCharacter(options);
  }

  /**
   * 更新人物移动 - 兼容接口，转发到工厂
   * @param {number} deltaTime 时间差
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @param {Object} navigationGraph 导航图
   */
  updateCharacters(deltaTime, tileWidth, tileHeight, mapWidth, mapHeight, navigationGraph) {
    this.characterFactory.updateCharacters(deltaTime, tileWidth, tileHeight, mapWidth, mapHeight, navigationGraph);
  }



  /**
   * 根据ID获取建筑数据 - 兼容接口，转发到工厂
   * @param {string} buildingId 建筑ID
   * @returns {Object|null} 建筑数据
   */
  getBuildingById(buildingId) {
    return this.characterFactory.getBuildingById(buildingId);
  }

  /**
   * 清理人物数据，但保留纹理缓存 - 兼容接口，转发到工厂
   */
  clearCharacters() {
    this.characterFactory.clearCharacters();
  }

  /**
   * 清理资源 - 兼容接口，转发到工厂
   */
  dispose() {
    this.characterFactory.dispose();
  }

  /**
   * 人物工作移动 - 兼容接口，转发到行为控制器
   * @param {Object} character 人物数据
   * @param {number} elapsedTime 经过的时间（秒）
   * @returns {boolean} 是否已到达目标位置
   */
  moveToWork(character, elapsedTime) {
    return this.behaviorController.moveToWork(character, elapsedTime);
  }

  /**
   * 人物随机移动 - 兼容接口，转发到行为控制器
   * @param {Object} character 人物数据
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @param {number} mapWidth 地图宽度
   * @param {number} mapHeight 地图高度
   * @returns {boolean} 是否成功开始移动
   */
  moveRandomly(character, tileWidth, tileHeight, mapWidth, mapHeight) {
    return this.behaviorController.moveRandomly(character, tileWidth, tileHeight, mapWidth, mapHeight);
  }

  /**
   * 在室内随机移动 - 兼容接口，转发到行为控制器
   * @param {Object} character 人物数据
   */
  moveRandomInRoom(character) {
    this.behaviorController.moveRandomInRoom(character);
  }

  /**
   * 检查从起点到终点的直线路径上是否有建筑物阻挡 - 兼容接口，转发到行为控制器
   * @param {number} startX 起点X网格坐标
   * @param {number} startY 起点Y网格坐标
   * @param {number} endX 终点X网格坐标
   * @param {number} endY 终点Y网格坐标
   * @returns {boolean} 是否有阻挡
   */
  hasObstacleInPath(startX, startY, endX, endY) {
    return this.behaviorController.hasObstacleInPath(startX, startY, endX, endY);
  }
  
  /**
   * 使用Bresenham算法获取两点之间的所有网格点 - 兼容接口，转发到行为控制器
   * @param {number} x0 起点X
   * @param {number} y0 起点Y
   * @param {number} x1 终点X
   * @param {number} y1 终点Y
   * @returns {Array} 路径上的所有网格点
   */
  getLinePoints(x0, y0, x1, y1) {
    return this.behaviorController.getLinePoints(x0, y0, x1, y1);
  }
  
  /**
   * 检查指定网格位置是否为障碍物 - 兼容接口，转发到行为控制器
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为障碍物
   */
  isObstacle(gridX, gridY) {
    return this.behaviorController.isObstacle(gridX, gridY);
  }
  
  /**
   * 使用A*算法寻找从起点到终点的最短路径 - 兼容接口，转发到行为控制器
   * @param {number} startX 起点X网格坐标
   * @param {number} startY 起点Y网格坐标
   * @param {number} endX 终点X网格坐标
   * @param {number} endY 终点Y网格坐标
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Array} 路径点数组，每个点包含{x,y}像素坐标
   */
  findPath(startX, startY, endX, endY, tileWidth, tileHeight) {
    return this.behaviorController.findPath(startX, startY, endX, endY, tileWidth, tileHeight);
  }
  

  
  /**
   * 清理路径缓存 - 兼容接口，转发到行为控制器
   */
  clearPathCache() {
    this.behaviorController.clearPathCache();
  }

  /**
   * 检查是否存在碰撞，并返回新的可行位置 - 兼容接口，转发到行为控制器
   * @param {number} x 目标x坐标
   * @param {number} y 目标y坐标
   * @param {string} characterId 当前角色ID
   * @param {number} tileWidth 瓦片宽度
   * @param {number} tileHeight 瓦片高度
   * @returns {Object} 安全的位置坐标
   */
  checkAndResolveCollisions(x, y, characterId, tileWidth, tileHeight) {
    return this.behaviorController.checkAndResolveCollisions(x, y, characterId, tileWidth, tileHeight);
  }

  /**
   * 判断指定位置是否为装饰物区域 - 兼容接口，转发到行为控制器
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为装饰物区域
   */
  isOnDecoration(gridX, gridY) {
    return this.behaviorController.isOnDecoration(gridX, gridY);
  }

  /**
   * 判断指定位置是否为道路 - 兼容接口，转发到行为控制器
   * @param {number} gridX 网格X坐标
   * @param {number} gridY 网格Y坐标
   * @returns {boolean} 是否为道路
   */
  isOnRoad(gridX, gridY) {
    return this.behaviorController.isOnRoad(gridX, gridY);
  }
}

export default CharacterRenderer; 