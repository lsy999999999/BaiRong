import { useGameStore } from '../../stores/gameStore';

class SendEvent {
    constructor() {}

    /**
     * 转换游戏速度（1-5对应5-1）
     * @param {number} rawGameSpeed - 原始游戏速度
     * @returns {number} - 转换后的游戏速度
     */
    convertGameSpeed(rawGameSpeed) {
        return 6 - rawGameSpeed; // 1→5, 2→4, 3→3, 4→2, 5→1
    }

    sendStartEvent(event) {
        const characters = this.gameStore.characters;
        const target_id = event.target_id;
        const target_character = characters.find(char => char.agentId === target_id);

        if (!target_character) {
            console.warn(`未找到目标角色，ID: ${target_id}`);
            return;
        }

        target_character.isWorking = 4;
        target_character.targetX = target_character.x;
        target_character.targetY = target_character.y;

        const rawGameSpeed = this.gameStore.gameSpeed;
        const gameSpeed = this.convertGameSpeed(rawGameSpeed);

        setTimeout(() => {
            target_character.isWorking = 0;
        }, 1000 * 5 * gameSpeed);
    }

    sendInformationGeneratedEvent(event) {
        const source_id = event.source_id;
        const target_id = event.target_id;

        // 如果源和目标是同一个角色，转发给sendStartEvent处理
        if (source_id === target_id) {
            console.log(`源和目标相同(ID: ${source_id})，转发给sendStartEvent处理`);
            this.sendStartEvent(event);
            return;
        }

        // 根据source_id和target_id获取人物
        const characters = this.gameStore.characters;
        const source_character = characters.find(char => char.agentId === source_id);
        const target_character = characters.find(char => char.agentId === target_id);

        // 获取游戏速度并转换
        const rawGameSpeed = this.gameStore.gameSpeed;
        const gameSpeed = this.convertGameSpeed(rawGameSpeed);

        // 分别检查source_character和target_character
        if (!source_character && !target_character) {
            // console.warn(`未找到源角色(${source_id})和目标角色(${target_id})`);
            return;
        }

        // 如果只有source_character存在
        if (source_character && !target_character) {
            // console.warn(`未找到目标角色(${target_id})，只对源角色(${source_id})执行操作`);
            source_character.isWorking = 4;
            source_character.targetX = source_character.x;
            source_character.targetY = source_character.y;

            setTimeout(() => {
                source_character.isWorking = 0;
            }, 1000 * 5 * gameSpeed);
            return;
        }

        // 如果只有target_character存在
        if (!source_character && target_character) {
            // console.warn(`未找到源角色(${source_id})，只对目标角色(${target_id})执行操作`);
            target_character.isWorking = 4;
            target_character.targetX = target_character.x;
            target_character.targetY = target_character.y;

            setTimeout(() => {
                target_character.isWorking = 0;
            }, 1000 * 5 * gameSpeed);
            return;
        }

        // 检查是否有任何一方在室内
        if (source_character.isIndoor || target_character.isIndoor) {
            // 如果有任何一方在室内，则双方原地不动，但标记为打电话状态
            source_character.isWorking = 1; // 1表示正在打电话
            target_character.isWorking = 1; // 1表示正在打电话

            // 停留时间根据游戏速度调整，基础时间为5秒
            setTimeout(() => {
                source_character.isWorking = 0;
                target_character.isWorking = 0;
            }, 1000 * 5 * gameSpeed);
            return;
        }

        // 获取人物的位置
        const source_position = {
            x: source_character.x,
            y: source_character.y
        };
        const target_position = {
            x: target_character.x,
            y: target_character.y
        };

        // 计算方向向量
        const dx = target_position.x - source_position.x;
        const dy = target_position.y - source_position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // 如果距离太近(小于2个瓦片宽度)，则不需要移动
        if (distance < 256) {
            // 原地不动，但仍然标记为工作状态
            source_character.isWorking = 2;
            target_character.isWorking = 2;

            // 停留时间根据游戏速度调整，基础时间为5秒
            setTimeout(() => {
                source_character.isWorking = 0;
                target_character.isWorking = 0;
            }, 1000 * 5 * gameSpeed);
            return;
        }

        // 如果距离非常远(大于20个瓦片宽度)，也不移动
        if (distance > 2560) {
            // 原地不动，但仍然标记为工作状态
            source_character.isWorking = 2; // 2表示远距离交流
            target_character.isWorking = 2; // 2表示远距离交流

            // 停留时间根据游戏速度调整，基础时间为5秒
            setTimeout(() => {
                source_character.isWorking = 0;
                target_character.isWorking = 0;
            }, 1000 * 5 * gameSpeed);
            return;
        }

        // 计算两个人物之间的中点作为会面点
        const midPointX = source_position.x + dx * 0.5;
        const midPointY = source_position.y + dy * 0.5;

        // 将中点转换为网格坐标
        const midGridX = Math.floor(midPointX / 128);
        const midGridY = Math.floor(midPointY / 128);

        // 寻找合适的会面点（非建筑物格子）
        let meetingPoint = this.findSuitableMeetingPoint(midGridX, midGridY);

        // 如果找不到合适的会面点，让角色保持原地
        if (!meetingPoint) {
            console.log("无法找到合适的会面点，角色将保持原位");

            // 标记为远距离交流
            source_character.isWorking = 2;
            target_character.isWorking = 2;

            // 设置目标为自身位置（原地不动）
            source_character.targetX = source_position.x;
            source_character.targetY = source_position.y;
            target_character.targetX = target_position.x;
            target_character.targetY = target_position.y;

            // 设置目标网格坐标
            source_character.targetGridX = Math.floor(source_character.targetX / 128);
            source_character.targetGridY = Math.floor(source_character.targetY / 128);
            target_character.targetGridX = Math.floor(target_character.targetX / 128);
            target_character.targetGridY = Math.floor(target_character.targetY / 128);

            // 停留时间
            setTimeout(() => {
                source_character.isWorking = 0;
                target_character.isWorking = 0;
            }, 1000 * 5 * gameSpeed);

            return;
        }

        // 将网格坐标转换为像素坐标（取格子中心点）
        const meetingPointX = meetingPoint.x * 128 + 64;
        const meetingPointY = meetingPoint.y * 128 + 64;

        // console.log(`设置会面点: (${meetingPoint.x},${meetingPoint.y}) => (${meetingPointX},${meetingPointY})`);

        // 设置源角色和目标角色的目标位置
        source_character.targetX = meetingPointX;
        source_character.targetY = meetingPointY;
        target_character.targetX = meetingPointX;
        target_character.targetY = meetingPointY;

        // 设置目标网格坐标（相同的会面点）
        source_character.targetGridX = meetingPoint.x;
        source_character.targetGridY = meetingPoint.y;
        target_character.targetGridX = meetingPoint.x;
        target_character.targetGridY = meetingPoint.y;

        // 标记为正在工作并需要移动
        source_character.isWorking = 3; // 3表示移动中交流
        target_character.isWorking = 3; // 3表示移动中交流

        // 清空之前的路径点，确保重新计算路径
        source_character.pathPoints = [];
        target_character.pathPoints = [];

        // 明确设置isMoving为true，触发移动
        source_character.isMoving = true;
        target_character.isMoving = true;

        // 强制触发路径计算，确保使用CharacterBehavior中的避障系统
        source_character.needsPathfinding = true;
        target_character.needsPathfinding = true;

        // 停留时间根据游戏速度调整，基础时间为5秒
        setTimeout(() => {
            source_character.isWorking = 0;
            target_character.isWorking = 0;
        }, 1000 * 5 * gameSpeed);
    }

    /**
     * 寻找合适的会面点（非建筑物格子）
     * @param {number} startX - 起始X网格坐标
     * @param {number} startY - 起始Y网格坐标
     * @returns {Object|null} - 合适的会面点坐标 {x, y}，如果找不到则返回null
     */
    findSuitableMeetingPoint(startX, startY) {
        // 先检查起始点是否是建筑物
        const startKey = `${startX},${startY}`;
        if (!window.gridToBuildingMap.has(startKey)) {
            return { x: startX, y: startY }; // 起始点不是建筑物，直接返回
        }

        // 从起始点开始向外搜索的最大距离
        const maxSearchRadius = 5;

        // 定义搜索方向：上、右、下、左、右上、右下、左下、左上
        const directions = [
            { dx: 0, dy: -1 }, // 上
            { dx: 1, dy: 0 }, // 右
            { dx: 0, dy: 1 }, // 下
            { dx: -1, dy: 0 }, // 左
            { dx: 1, dy: -1 }, // 右上
            { dx: 1, dy: 1 }, // 右下
            { dx: -1, dy: 1 }, // 左下
            { dx: -1, dy: -1 } // 左上
        ];

        // 螺旋搜索：从内向外扩展搜索范围
        for (let radius = 1; radius <= maxSearchRadius; radius++) {
            // 遍历当前半径的所有格子
            for (let dx = -radius; dx <= radius; dx++) {
                // 只检查当前半径的边界，而不是填充整个正方形
                for (let dy = -radius; dy <= radius; dy++) {
                    // 只考虑边界上的格子
                    if (Math.abs(dx) === radius || Math.abs(dy) === radius) {
                        const gridX = startX + dx;
                        const gridY = startY + dy;
                        const gridKey = `${gridX},${gridY}`;

                        // 检查该格子是否不是建筑物
                        if (!window.gridToBuildingMap.has(gridKey)) {
                            return { x: gridX, y: gridY };
                        }
                    }
                }
            }
        }

        // 如果搜索范围内没有找到合适的格子，返回null
        return null;
    }
}

export default class EventModalProcess extends SendEvent {
    constructor() {
        super();
        this.currentIndex = 0;
        this.initGameStore();
        this.isDev = true;
        this.intervalId = null;
        this.start();
    }

    initGameStore() {
        this.gameStore = useGameStore();
    }

    getSpeed() {
        const rawSpeed = this.gameStore.gameSpeed;
        return rawSpeed; // 这里不反转，因为是用于事件处理速度，而不是持续时间
    }

    getEventData() {
        return this.gameStore.eventsOriginalData;
    }

    getIsPaused() {
        return this.gameStore.isPaused;
    }
    start() {
        if (this.intervalId) return;
        this.intervalId = setInterval(() => {
            if (this.getIsPaused()) return
            const eventsData = this.getEventData();
            const speed = this.getSpeed();
            const newEvents = eventsData.slice(this.currentIndex, this.currentIndex + Math.ceil(speed));

            newEvents.forEach((event, index) => {
                // 计算当前事件在原始数据中的实际索引
                const currentEventIndex = this.currentIndex + index;

                // 如果当前事件的索引小于原始数据的总长度，说明不是重复数据
                if (currentEventIndex < eventsData.length) {
                    // 检查该事件是否已存在于eventsData中
                    // 假设事件有唯一标识符，如id或timestamp
                    const isDuplicate = this.gameStore.eventsData.some(existingEvent => {
                        // 如果事件有唯一ID，可以直接比较ID
                        if (event.id && existingEvent.id) {
                            return event.id === existingEvent.id;
                        }
                        // 如果事件有时间戳和类型，可以联合比较
                        if (event.timestamp && event.event_type) {
                            return event.timestamp === existingEvent.timestamp &&
                                event.event_type === existingEvent.event_type &&
                                event.source_id === existingEvent.source_id &&
                                event.target_id === existingEvent.target_id;
                        }
                        // 退化情况：使用字符串比较（性能较低）
                        return JSON.stringify(event) === JSON.stringify(existingEvent);
                    });
                    // 如果不是重复数据，则添加到eventsData
                    if (!isDuplicate) {
                        this.gameStore.eventsData.push(event);
                    }
                }

                if (event.event_type === "StartEvent") {
                    this.sendStartEvent(event);
                } else {
                    this.sendInformationGeneratedEvent(event);
                }
            });

            this.currentIndex += newEvents.length;
        }, 1000);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}