import { fa, tr } from 'element-plus/es/locale/index.mjs';
import { defineStore } from 'pinia'

/**
 * 游戏状态管理
 * 管理游戏的暂停与开始状态以及游戏速度
 */
export const useGameStore = defineStore('game', {
    state: () => ({

        isPaused: true, // 游戏是否暂停
        gameSpeed: 0.5, // 游戏速度倍率：1倍速或3倍速

        // PIXI应用实例
        pixiApp: null, // 存储PIXI应用实例
        viewport: null, // 存储视口实例
        cameraController: null, // 存储相机控制器

        // 人口相关状态
        populationTotal: 200, // 人口总数上限
        populationCreated: 0, // 已创建的人口数量
        populationOutdoor: 0, // 室外人口数量
        populationSize: 300, // 每次生成的人口数量
        unitCapacity: 2, // 每单位宽度的人物容量值

        // 人物数据
        characters: [], // 存储所有人物实例（室内和室外）
        focusedCharacterId: null, // 当前焦点关注的角色ID

        // 开发者模式状态
        isDevMode: false, // 是否启用开发者模式
        // 设置状态
        isSettingComplete: false, // 设置是否完成
        isStart: false, // 是否开始

        // 建筑物网格数据Map，替代window.gridToBuildingMap
        // 存储格式为: {gridX,gridY} -> buildingId
        // 这个数据来源于TilemapRenderer.vue中的gridToBuildingMap变量
        buildingData: new Map(),

        // 建筑物原始数据，存储props.mapData.buildingData
        buildingOriginalData: [],

        // 新增：建筑对象数组，类似于characters数组
        buildings: [],

        // 系统配置
        systemConfig: [],

        // agents数据
        agentsData: [],
        //events数据
        eventsData: [],
        //events原始数据
        eventsOriginalData: [],
    }),

    getters: {
        // 游戏是否正在运行（未暂停）
        isRunning: (state) => state.isStart,

        // 获取当前游戏速度
        currentSpeed: (state) => state.gameSpeed,

        // 获取PIXI应用实例
        getPixiApp: (state) => state.pixiApp,

        // 获取视口实例
        getViewport: (state) => state.viewport,

        // 获取相机控制器
        getCameraController: (state) => state.cameraController,

        // 获取剩余可生成人口数量
        remainingPopulation: (state) => state.populationTotal - state.populationCreated,

        // 检查是否已达到人口上限
        isPopulationFull: (state) => state.populationCreated >= state.populationTotal,

        // 获取开发者模式状态
        devModeEnabled: (state) => state.isDevMode,

        // 获取单位容量值
        getUnitCapacity: (state) => state.unitCapacity,

        // 获取所有人物
        getAllCharacters: (state) => state.characters,

        // 获取室内人物
        getIndoorCharacters: (state) => state.characters.filter(char => char.isIndoor),

        // 获取室外人物
        getOutdoorCharacters: (state) => state.characters.filter(char => !char.isIndoor),

        // 获取设置完成状态
        getSettingComplete: (state) => state.isSettingComplete,

        // 获取系统配置
        getSystemConfig: (state) => state.systemConfig,

        // 获取agents数据
        getAgentsData: (state) => state.agentsData,

        // 获取events数据
        getEventsData: (state) => state.eventsData,

        // 获取当前焦点角色ID
        getFocusedCharacterId: (state) => state.focusedCharacterId,

        // 获取当前焦点角色对象
        getFocusedCharacter: (state) => {
            if (!state.focusedCharacterId) return null;
            return state.characters.find(char => char.agentId === state.focusedCharacterId);
        },

        // 检查指定网格位置是否有建筑
        hasBuildingAt: (state) => (gridX, gridY) => {
            return state.buildingData.has(`${gridX},${gridY}`);
        },

        // 获取指定网格位置的建筑ID
        getBuildingAt: (state) => (gridX, gridY) => {
            return state.buildingData.get(`${gridX},${gridY}`);
        },

        // 新增：获取所有建筑
        getAllBuildings: (state) => state.buildings,

        // 新增：根据ID获取建筑
        getBuildingById: (state) => (buildingId) => {
            return state.buildings.find(building => building.buildingId === buildingId);
        },

        // 新增：根据坐标获取建筑对象
        getBuildingByCoordinates: (state) => (x, y) => {
            const buildingId = state.buildingData.get(`${x},${y}`);
            if (buildingId) {
                return state.buildings.find(building => building.buildingId === buildingId);
            }
            return null;
        }
    },

    actions: {
        // 暂停游戏
        pauseGame() {
            this.isPaused = true;
            console.log('游戏已暂停');
        },

        // 继续游戏
        resumeGame() {
            this.isPaused = false;
            console.log('游戏已继续');
        },

        // 切换游戏暂停/继续状态
        togglePause() {
            this.isPaused = !this.isPaused;
            console.log(`游戏${this.isPaused ? '已暂停' : '已继续'}`);
        },

        // 设置游戏速度
        setGameSpeed(speed) {
            if (speed >= 1 && speed <= 5) {
                this.gameSpeed = speed;
                console.log(`游戏速度已设置为${speed}倍速`);
            } else {
                console.warn('游戏速度只能设置为1-5倍速之间');
            }
        },

        // 切换游戏速度（在1、2、3、4、5之间循环切换）
        toggleGameSpeed() {
            this.gameSpeed = Math.ceil(this.gameSpeed) < 5 ? this.gameSpeed + 1 : 0.5;
            console.log(`游戏速度已切换为${this.gameSpeed}倍速`);
        },

        // 初始化开发者模式（从localStorage读取）
        initDevMode() {
            try {
                // 不从localStorage读取，使用代码中定义的初始状态
                // 只将当前状态保存到localStorage，而不是从中读取
                localStorage.setItem('devmode', this.isDevMode ? 'true' : 'false');
                console.log(`开发者模式初始化为: ${this.isDevMode ? '已启用' : '已禁用'}`);
            } catch (error) {
                console.error('初始化开发者模式时出错:', error);
                // 出错时默认为false
                this.isDevMode = false;
            }
        },

        // 设置开发者模式
        setDevMode(enabled) {
            this.isDevMode = enabled;
            // 同步到localStorage，保持兼容性
            localStorage.setItem('devmode', enabled ? 'true' : 'false');
            console.log(`开发者模式已${enabled ? '启用' : '禁用'}`);
        },

        // 切换开发者模式
        toggleDevMode() {
            this.isDevMode = !this.isDevMode;
            // 同步到localStorage，保持兼容性
            localStorage.setItem('devmode', this.isDevMode ? 'true' : 'false');
            console.log(`开发者模式已${this.isDevMode ? '启用' : '禁用'}`);
        },

        // 设置人口总数上限
        setPopulationTotal(total) {
            console.log("setPopulationTotal", total);
            if (total >= 1 && total <= 50000) {
                this.populationTotal = total;
                console.log(`人口总数上限已设置为${total}`);

                // 同步到window全局变量
                if (typeof window !== 'undefined') {
                    window.cityMapPopulationTotal = total;
                }
            } else {
                console.warn('人口总数只能在1000-50000之间设置');
            }
        },

        // 设置每次生成的人口数量
        setPopulationSize(size) {
            if (size >= 100 && size <= 1000) {
                this.populationSize = size;
                console.log(`每次生成人口数量已设置为${size}`);

                // 同步到window全局变量
                if (typeof window !== 'undefined') {
                    window.cityMapPopulationSize = size;
                }
            } else {
                console.warn('每次生成人口数量只能在100-1000之间设置');
            }
        },

        // 增加已创建人口数量
        addPopulationCreated(count = 1) {
            this.populationCreated += count;
            console.log(`已增加${count}个人口，当前总人数: ${this.populationCreated}`);

            // 同步到window全局变量
            if (typeof window !== 'undefined') {
                window.cityMapPopulationCreated = this.populationCreated;
            }
        },

        // 重置已创建人口数量
        resetPopulationCreated() {
            this.populationCreated = 0;
            console.log('已重置人口计数');

            // 同步到window全局变量
            if (typeof window !== 'undefined') {
                window.cityMapPopulationCreated = 0;
            }
        },

        // 设置单位容量值
        setUnitCapacity(capacity) {
            if (capacity >= 1 && capacity <= 20) {
                this.unitCapacity = capacity;
                console.log(`单位容量值已设置为${capacity}`);

                // 同步到window全局变量
                if (typeof window !== 'undefined') {
                    window.cityMapUnitCapacity = capacity;
                }
            } else {
                console.warn('单位容量值只能在1-20之间设置');
            }
        },

        // 添加单个人物到列表
        addCharacter(character) {
            // 添加isVisible属性，初始为false
            if (!character.hasOwnProperty('isVisible')) {
                character.isVisible = false;
            }

            this.characters.push(character);
        },

        // 批量添加人物到列表
        addCharacters(characterArray) {
            this.characters.push(...characterArray);
        },

        // 根据ID获取人物
        getCharacterById(id) {
            return this.characters.find(char => char.id === id);
        },

        // 根据ID更新人物数据
        updateCharacter(id, data) {
            const index = this.characters.findIndex(char => char.id === id);
            if (index !== -1) {
                this.characters[index] = {...this.characters[index], ...data };
            }
        },

        // 根据ID删除人物
        removeCharacter(id) {
            const index = this.characters.findIndex(char => char.id === id);
            if (index !== -1) {
                this.characters.splice(index, 1);
            }
        },

        // 清空所有人物
        clearCharacters() {
            this.characters = [];
        },

        // 设置全部人物列表
        setCharacters(characters) {
            this.characters = characters;
        },

        // 设置配置完成状态
        setSettingComplete(isComplete) {
            this.isSettingComplete = isComplete;
            console.log(`设置状态已${isComplete ? '完成' : '重置'}`);
        },

        // 更新系统配置
        updateSystemConfig(config) {
            this.systemConfig = {...this.systemConfig, ...config };
            console.log('系统配置已更新');
        },

        // 设置当前焦点角色ID
        setFocusedCharacterId(id) {
            this.focusedCharacterId = id;

            // 更新所有角色的isFocused状态
            this.characters.forEach(char => {
                // 比较agentId而不是id，确保正确匹配角色
                const isFocused = char.agentId === id;
                char.isFocused = isFocused;

                // 不在这里处理可见性，移至updateCameraFollow方法中
            });

            console.log(`已设置焦点角色ID: ${id || '无'}`);
        },

        // 清除当前焦点角色ID
        clearFocusedCharacterId(previousId = null) {
            // 获取要清除的角色ID
            const targetId = previousId || this.focusedCharacterId;

            // 如果没有目标ID，直接返回
            if (!targetId) return;

            // 获取目标焦点角色信息
            const focusedCharacter = this.characters.find(char => char.agentId === targetId);

            // 处理目标焦点角色所在建筑物的可见性
            if (focusedCharacter && focusedCharacter.isIndoor && focusedCharacter.sprite) {
                // 获取室内地板和楼层精灵
                const roomSprite = focusedCharacter.sprite.parent; // 室内地板
                const floorSprite = roomSprit.parent; // 楼层精灵

                // 隐藏室内地板
                if (roomSprite) {
                    roomSprite.visible = false;

                    // 隐藏室内地板上的所有人物
                    if (roomSprite.indoorCharacters) {
                        roomSprite.indoorCharacters.forEach(character => {
                            character.visible = false;
                        });
                    }
                }

                // 恢复楼层精灵的透明度和zIndex
                if (floorSprite) {
                    // 恢复原始zIndex
                    if (floorSprite.originalZIndex !== undefined) {
                        floorSprite.zIndex = floorSprite.originalZIndex;
                        delete floorSprite.originalZIndex;
                    }
                }
            }

            // 清除所有角色的isFocused状态
            this.characters.forEach(char => {
                char.isFocused = false;
            });

            // 仅当清除当前焦点角色时，才设置为null
            if (!previousId) {
                this.focusedCharacterId = null;
                console.log('已清除焦点角色ID');
            } else {
                console.log(`已清除角色ID ${previousId} 的焦点状态`);
            }
        },

        // 设置建筑数据Map
        setBuildingData(buildingDataMap) {
            this.buildingData = buildingDataMap;
            console.log('已更新建筑数据Map');
        },

        // 添加建筑数据
        addBuildingData(gridKey, buildingId) {
            this.buildingData.set(gridKey, buildingId);
        },

        // 清空建筑数据
        clearBuildingData() {
            this.buildingData.clear();
            console.log('已清空建筑数据Map');
        },

        // 设置原始建筑数据数组
        setBuildingOriginalData(buildingDataArray) {
            this.buildingOriginalData = buildingDataArray;
            console.log('已更新原始建筑数据数组', this.buildingOriginalData);
        },

        // 新增：设置建筑对象数组
        setBuildings(buildings) {
            this.buildings = buildings;
            console.log(`已设置${buildings.length}个建筑对象`);
        },

        // 新增：添加单个建筑到数组
        addBuilding(building) {
            this.buildings.push(building);
        },

        // 新增：批量添加建筑到数组
        addBuildings(buildingArray) {
            this.buildings.push(...buildingArray);
        },

        // 新增：根据ID更新建筑数据
        updateBuilding(buildingId, data) {
            const index = this.buildings.findIndex(building => building.buildingId === buildingId);
            if (index !== -1) {
                this.buildings[index] = {...this.buildings[index], ...data };
            }
        },

        // 新增：根据ID删除建筑
        removeBuilding(buildingId) {
            const index = this.buildings.findIndex(building => building.buildingId === buildingId);
            if (index !== -1) {
                this.buildings.splice(index, 1);
            }
        },

        // 新增：清空所有建筑
        clearBuildings() {
            this.buildings = [];
            console.log('已清空所有建筑数据');
        },

        // 设置PIXI应用实例
        setPixiApp(app) {
            this.pixiApp = app;
            console.log('已设置PIXI应用实例');
        },

        // 设置视口实例
        setViewport(viewport) {
            this.viewport = viewport;
            console.log('已设置视口实例');
        },

        // 设置相机控制器
        setCameraController(controller) {
            this.cameraController = controller;
            console.log('已设置相机控制器');
        },

        // 清理PIXI资源
        clearPixiResources() {
            if (this.viewport) {
                this.viewport.destroy();
                this.viewport = null;
            }

            if (this.pixiApp) {
                this.pixiApp.destroy(true, { children: true, texture: true, baseTexture: true });
                this.pixiApp = null;
            }

            console.log('已清理PIXI资源');
        },

        // 重置所有状态
        resetState() {
            // 重置游戏状态
            this.isPaused = true;
            this.gameSpeed = 0.5;
            this.isStart = false;

            // 清理PIXI相关实例
            this.clearPixiResources();
            this.pixiApp = null;
            this.viewport = null;
            this.cameraController = null;

            // 重置人口相关数据
            this.populationTotal = 200;
            this.populationCreated = 0;
            this.populationOutdoor = 0;
            this.populationSize = 300;
            this.unitCapacity = 2;

            // 清空人物数据
            this.characters = [];
            this.focusedCharacterId = null;

            // 不重置开发者模式状态(isDevMode保持不变)

            // 重置设置状态
            this.isSettingComplete = false;

            // 清空建筑物数据
            this.buildingData = new Map();
            this.buildingOriginalData = [];
            this.buildings = [];

            // 清空系统配置
            this.systemConfig = [];

            // 清空agents和events数据
            this.agentsData = [];
            this.eventsData = [];
            this.eventsOriginalData = [];

            console.log('游戏状态已完全重置');
        }
    }
})