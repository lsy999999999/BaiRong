<template>
  <div class="chat-mode-layout">
    <div class="chat-area">
      <div class="messages-list">
        <div v-for="(message, index) in messages" :key="index" class="message" :class="message.sender">
          <div class="message-content">
            <div class="message-sender">
              {{ message.sender === "user" ? "You" : "AI Assistant" }}
            </div>
            <div class="message-text" v-html="message.content"></div>
          </div>
        </div>
        <div v-if="isLoading" class="message ai loading-message">
          <div class="message-content">
            <div class="message-sender">AI Assistant</div>
            <div class="thinking-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <div class="textarea-container chat-textarea">
          <textarea v-model="queryInput" placeholder="Type your message here..." rows="1"
            @keyup.ctrl.enter="handleSubmit" :disabled="isLoading"></textarea>
          <!-- <button class="submit-btn" @click="handleSubmit" :disabled="isLoading || isback"> -->
          <!-- 现在返回的时候也可以输入 -->
          <button class="submit-btn" @click="handleSubmit" :disabled="isLoading">
            <i class="fa fa-arrow-right"></i> {{ isLoading ? "Wait..." : "Send" }}
          </button>
        </div>
      </div>
    </div>

    <div class="summary-panel">
      <div class="summary-header">
        <h3>Multi-Agent System ODD Protocol</h3>
      </div>

      <div v-if="oddSummaryGenerated" class="scenario-name-container">
        <label for="scenario-name">Scenario Name:</label>
        <!-- <input type="text" id="scenario-name" v-model="scenarioName" placeholder="Enter scenario name..."
          class="scenario-name-input" :disabled="isback" /> -->
        <!-- 现在返回的时候用户也可以修改 -->
        <input type="text" id="scenario-name" v-model="scenarioName" placeholder="Enter scenario name..."
          class="scenario-name-input" />
        <div class="name-hint">
          You can modify this name as needed. Changes will be automatically saved.
        </div>
      </div>

      <div class="summary-content">
        <div v-html="summaryContent"></div>
      </div>

      <div class="summary-footer" v-if="canProceed">
        <button class="next-btn" @click="proceedToNextStepVerification">
          Proceed to Next Step <i class="fa fa-arrow-right"></i>
        </button>
      </div>
    </div>
    <!-- <el-dialog v-model="new_scene_nameWin" title="Change the scene name" width="30%">
      <el-form :model="winform">
        <el-form-item label="New scene name" label-width="120px">
          <el-input v-model="new_scene_name" autocomplete="off" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="new_scene_nameWin = false">Cancel</el-button>
          <el-button type="primary" @click="new_scene_nameWin = false">
            Confirm
          </el-button>
        </div>
      </template>
    </el-dialog> -->
  </div>
</template>

<script>
import axios from "axios";
import { ElMessageBox, ElMessage } from "element-plus";
import { nextTick } from 'vue';
export default {
  name: "ChatMode",
  data() {
    return {
      queryInput: "", // 用户输入的查询文本
      messages: [], // 聊天消息历史记录数组
      isLoading: false, // 加载状态标志，用于显示加载动画
      summaryContent: "", // 总结面板的内容
      initialQuery: "", // 初始查询参数，从路由中获取
      scenarioName: "", // 场景名称
      oddSummaryGenerated: false, // ODD协议摘要是否已生成的标志
      sessionId: "", // 与后端通信的会话ID
      toNext: false, // 是否可以进入下一步的标志
      isback: false, // 是否是通过返回按钮返回的标志
      new_scene_nameWin:false,//新场景名称对话框
      new_scene_name:"",//新场景名称
      winform:{},
    };
  },
  computed: {
    canProceed() {
      // 确保与ProgressLayoutWrapper中的判断条件一致
      // 计算属性：判断是否可以进入下一步
      return this.toNext;
    },
  },
  created() {
    let queryParam = this.$route.query;
    // 如果存在缓存数据，则直接使用
    // 如果存在就说明是从第三步返回的
    // if (window.summaryContent && window.messages) {
    //   this.summaryContent = window.summaryContent
    //   this.messages = window.messages
    //   this.scenarioName = localStorage.getItem("scenarioName")
    //   if (this.scenarioName) {
    //     this.isback = true;
    //     this.$emit("update:canProceed", true);
    //   }
    //   this.oddSummaryGenerated = true;
    //   this.toNext = true
    // } else 
    if (window.query) { // 如果有window.query全局变量，说明是从首页查询进来的，则使用该值请求接口
      this.initialQuery = window.query;
      // 添加用户消息到聊天记录
      this.addMessage("user", this.initialQuery);
      this.isLoading = true;
      // 请求接口
      this.generateMockResponse_start(this.initialQuery);
    } else {
      // 如果window.query为空，说明是刷新页面或者从第二步返回的，需要查询历史列表
      let sessionId = localStorage.getItem("sessionId")?localStorage.getItem("sessionId"):"None";
      let scenarioName = localStorage.getItem("scenarioName")?"?env_name="+localStorage.getItem("scenarioName"):"";
      axios.get('/api/odd/history/'+sessionId+scenarioName).then((response)=>{
        this.sessionId = response.data.session_id;
        this.messages = response.data.history;
      })
      axios.get('/api/odd/protocol/'+sessionId+scenarioName).then((response)=>{
        console.log(response.data, 'response.data');
        let messageData = response.data;
        if (messageData.odd_protocol) {
            this.summaryContent = ` <div class="protocol-section">
								<h4 class="capitalize-text">Design Concepts</h4>
								<p><strong class="capitalize-text">Communication Protocols:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.design_concepts.communication_protocols}</li>       
								</ul>
								<p><strong class="capitalize-text">Decision Mechanisms:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.design_concepts.decision_mechanisms}</li>       
								</ul>
								<p><strong class="capitalize-text">Interaction Patterns:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.design_concepts.interaction_patterns}</li>       
								</ul>
								<h4 class="capitalize-text">Details</h4>
								<p><strong class="capitalize-text">Agent Behaviors:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.details.agent_behaviors}</li>       
								</ul>
								<p><strong class="capitalize-text">Decision Algorithms:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.details.decision_algorithms}</li>       
								</ul>
								<p><strong class="capitalize-text">Specific Constraints:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.details.specific_constraints}</li>       
								</ul>
								<h4 class="capitalize-text">Overview</h4>
								<p><strong class="capitalize-text">Agent Types:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.overview.agent_types}</li>       
								</ul>
								<p><strong class="capitalize-text">Environment Description:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.overview.environment_description}</li>       
								</ul>
								<p><strong class="capitalize-text">System Goal:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.overview.system_goal}</li>       
								</ul>
								</div>`;
          }
          if (messageData) {
            this.toNext = true;
            this.scenarioName = localStorage.getItem("scenarioName");
            // 设置当前对话已生成ODD总结结果
            this.$nextTick(() => {
              this.oddSummaryGenerated = true;
            });
          }
      })

      // ElMessageBox.confirm(
      //   "No query content. Return to homepage?",
      //   "Notice",
      //   {
      //     confirmButtonText: "OK",
      //     cancelButtonText: "Cancel",
      //     type: "warning"
      //   }
      // ).then(() => {
      //   // 确认后返回仪表盘页面
      //   this.$router.push('/');
      // }).catch(() => {
      //   // 取消后也返回仪表盘页面，因为没有查询内容无法继续
      //   this.$router.push('/');
      // });
    }
  },
  methods: {
    handleSubmit() {
      // 处理用户提交消息的方法
      const query = this.queryInput.trim();

      if (!query) {
        // 如果输入为空，添加抖动动画提示用户
        const textarea = this.$el.querySelector(".textarea-container textarea");
        if (textarea) {
          textarea.classList.add("shake");
          setTimeout(() => {
            textarea.classList.remove("shake");
          }, 500);
        }
        return;
      }

      // 添加用户消息到聊天记录
      this.addMessage("user", query);
      this.queryInput = "";

      // 显示AI思考中动画
      this.isLoading = true;
      
      // 确保滚动到底部
      this.scrollToBottom();

      // 调用接口获取响应
      this.generateMockResponse(query);
    },
    simulateStreamingResponse(query, messageData) {
      // 模拟流式响应，实现打字机效果
      // 获取完整回复
      const fullResponse = messageData.message; //this.generateMockResponse(query);

      // 将回复分成单词以模拟流式效果
      console.log(fullResponse);
      const words = fullResponse.split(" ");
      let currentResponse = "";
      let wordIndex = 0;

      // 创建一个临时消息对象用于流式显示
      this.addMessage("ai", "");
      const messageIndex = this.messages.length - 1;

      // 模拟每隔一小段时间添加一组词
      const streamInterval = setInterval(() => {
        if (wordIndex < words.length) {
          // 一次添加多个词，加快显示速度
          const wordsToAdd = Math.min(5, words.length - wordIndex);
          for (let i = 0; i < wordsToAdd; i++) {
            currentResponse += (currentResponse ? " " : "") + words[wordIndex + i];
          }
          wordIndex += wordsToAdd;

          // 更新消息内容
          this.messages[messageIndex].content = currentResponse;

          // 滚动到最新消息
          this.scrollToBottom();
        } else {
          // 流式显示完成
          clearInterval(streamInterval);
          
          // 设置加载状态为false
          this.isLoading = false;

          // 确保最后滚动到底部
          this.$nextTick(() => {
            this.scrollToBottom();
          });

          // 如果返回数据中包含ODD协议信息，则更新摘要内容
          if (messageData.odd_protocol) {
            this.summaryContent = ` <div class="protocol-section">
								<h4 class="capitalize-text">Design Concepts</h4>
								<p><strong class="capitalize-text">Communication Protocols:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.design_concepts.communication_protocols}</li>       
								</ul>
								<p><strong class="capitalize-text">Decision Mechanisms:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.design_concepts.decision_mechanisms}</li>       
								</ul>
								<p><strong class="capitalize-text">Interaction Patterns:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.design_concepts.interaction_patterns}</li>       
								</ul>
								<h4 class="capitalize-text">Details</h4>
								<p><strong class="capitalize-text">Agent Behaviors:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.details.agent_behaviors}</li>       
								</ul>
								<p><strong class="capitalize-text">Decision Algorithms:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.details.decision_algorithms}</li>       
								</ul>
								<p><strong class="capitalize-text">Specific Constraints:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.details.specific_constraints}</li>       
								</ul>
								<h4 class="capitalize-text">Overview</h4>
								<p><strong class="capitalize-text">Agent Types:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.overview.agent_types}</li>       
								</ul>
								<p><strong class="capitalize-text">Environment Description:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.overview.environment_description}</li>       
								</ul>
								<p><strong class="capitalize-text">System Goal:</strong></p>
								<ul>
								    <li>${messageData.odd_protocol.overview.system_goal}</li>       
								</ul>
								</div>`;
          }

          // 如果对话已完成，允许进入下一步
          if (messageData.is_complete) {
            this.toNext = true;
            this.scenarioName = messageData.scene_name;
            // 设置当前对话已生成ODD总结结果
            this.$nextTick(() => {
              this.oddSummaryGenerated = true;
            });
          }

          // 向父组件传递场景名称更新
          this.$emit("update:scenarioName", this.scenarioName);

        }
      }, 20); // 20毫秒间隔，控制打字速度
    },
    addMessage(sender, content) {
      // 添加消息到聊天历史记录
      this.messages.push({
        sender, // 发送者：user或ai
        content, // 消息内容
        timestamp: new Date(), // 时间戳
      });
      
      // 添加消息后滚动到底部
      this.$nextTick(() => {
        this.scrollToBottom();
      });
    },
    // 添加滚动到底部的方法
    scrollToBottom() {
      const messagesList = this.$el.querySelector(".messages-list");
      if (messagesList) {
        messagesList.scrollTop = messagesList.scrollHeight;
      }
    },
    /**
     * 场景名称校验方法，如果存在则提示用户修改，如果不存在则继续下一步。
     */
    proceedToNextStepVerification(index = '0') {
      //如果是返回回来的就直接进入下一步
      // if(this.isback){
      //   this.proceedToNextStep();
      // }else{
        //判断场景名称是否存在
        axios.post("/api/check_scene_name", {
          scene_name: this.scenarioName,
        }).then((response) => {
          if (response.data.exists) {
            ElMessageBox.confirm(
              "The scene name is already in use. Do you want to continue? If so, the scene information will be reset",
              "Confirmation",
              {
                confirmButtonText: "OK",
                cancelButtonText: "Cancel",
              }
            ).then(() => {
              this.$msgbox.close();
              nextTick(() => {
                this.proceedToNextStep();
              });
            }).catch(() => {
              ElMessageBox.prompt('Please enter the new scene name', 'Tip', {
                confirmButtonText: 'OK',
                cancelButtonText: 'Cancel',
                inputValue: this.scenarioName
              }).then(({ value }) => {
                this.scenarioName = value;
                this.proceedToNextStepVerification()
              })
            })
          } else {
            this.proceedToNextStep();
          }
        });
      // }
      
    },
    check_scene_name() {
      let Repeat = '';
      axios
        .post("/api/check_scene_name", {
          scene_name: this.scenarioName,
        }).then((response) => {
          if (response.data.exists) {
            Repeat = truel
          }
        })
      return Repeat;
    },
    proceedToNextStep() {
      // 进入下一步的方法，显示确认对话框
      ElMessageBox.confirm(
        "Are you sure you want to proceed to the next step?",
        "Confirmation",
        {
          confirmButtonText: "OK",
          cancelButtonText: "Cancel",
        }
      ).then(() => {
        // 确认场景设置并继续
        // 如果是从第三步返回的，则不进行场景设置
        // if (this.isback) {
        //   this.$emit("step-complete");
        // } else {
          axios
            .post("/api/odd/confirm_scene", {
              session_id: this.sessionId?this.sessionId:localStorage.getItem("sessionId"),
              scene_name: this.scenarioName,
            })
            .then((response) => {
              if (response.data.success) {
                // 保存当前状态到全局变量和本地存储
                window.messages = this.messages
                window.summaryContent = this.summaryContent
                localStorage.setItem("scenarioName", this.scenarioName);
                // 触发step-complete事件通知父组件，并传递场景名称
                this.$emit("step-complete");
              } else {
                // 显示错误信息
                ElMessage({
                  message: response.data.message,
                  type: "info",
                });
              }
            });
        // }
      });
    },
    generateMockResponse_start(query) {
      // 初始化会话，发送第一个请求到后端
      axios
        .post("/api/odd/start", {
          prompt: query, // 用户输入的初始查询
          category: this.$route.query.category, // 从路由获取类别
          model_name: this.$route.query.model_name, // 从路由获取模型名称
        })
        .then((response) => {
          console.log(response.data, 'response')
          // 保存会话ID
          this.sessionId = response.data.session_id;
          localStorage.setItem("sessionId", this.sessionId);

          // 处理响应并显示
          this.simulateStreamingResponse(query, response.data);
        });
    },
    generateMockResponse(query) {
      // 发送用户消息到现有会话
      axios
        .post("/api/odd/chat", {
          session_id: this.sessionId?this.sessionId:localStorage.getItem("sessionId"), // 使用保存的会话ID
          message: query, // 用户输入的消息
        })
        .then((response) => {
          // 处理响应并显示
          this.simulateStreamingResponse(query, response.data);
        });
    },
  },
  watch: {
    oddSummaryGenerated: {
      handler(newValue) {
        // 监听ODD摘要生成状态的变化
        // 向父组件发送状态更新
        this.$emit("update:canProceed", newValue);
      },
      immediate: true, // 组件创建时立即执行一次
    },
    isLoading: {
      handler(newValue) {
        // 监听加载状态变化并向父组件发送
        this.$emit("update:loading", newValue);
      },
      immediate: true, // 组件创建时立即执行一次
    },
  },
  expose: ['proceedToNextStepVerification'],
};
</script>

<style scoped>
.chat-mode-layout {
  display: flex;
  flex-wrap: wrap;
  min-height: calc(100vh - 120px);
  /* 减去进度条和导航栏的高度 */
  background-color: var(--bg-color);
  position: relative;
}

.chat-area {
  flex: 3;
  height: calc(100vh - 180px);
  /* 减去进度条、导航栏和padding的高度 */
  display: flex;
  flex-direction: column;
  padding-right: 20px;
}

.messages-list {
  flex: 1;
  overflow-y: scroll;
  /* 改为scroll而不是auto，始终显示滚动条 */
  padding: 15px;
  padding-right: 20px;
  /* 增加右侧padding，为滚动条预留更多空间 */
  display: flex;
  flex-direction: column;
  gap: 15px;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  margin-bottom: 15px;
  scrollbar-gutter: stable;
  /* 现代浏览器支持的滚动条空间预留属性 */
}

.message {
  max-width: 80%;
  padding: 10px 15px;
  border-radius: 10px;
  animation: fadeIn 0.3s ease;
}

.message.user {
  align-self: flex-end;
  background-color: var(--accent-color);
  color: white;
}

.message.ai {
  align-self: flex-start;
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.loading-message {
  background-color: transparent;
}

.message-content {
  display: flex;
  flex-direction: column;
}

.message-sender {
  font-weight: bold;
  margin-bottom: 5px;
  font-size: 0.9rem;
  opacity: 0.8;
}

.message-text {
  line-height: 1.4;
}

/* 清除浏览器默认样式，确保AI返回内容排版统一 */
.message-text {
  /* 重置基本排版 */
  font-family: var(--font-family,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      Roboto,
      Oxygen,
      Ubuntu,
      Cantarell,
      "Open Sans",
      "Helvetica Neue",
      sans-serif);
  color: inherit;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message-text p,
.summary-content p {
  margin: 0.5em 0;
  padding: 0;
}

.message-text ul,
.message-text ol,
.summary-content ul,
.summary-content ol {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.message-text ul li,
.summary-content ul li {
  list-style-type: disc;
  margin: 0.25em 0;
}

.message-text ol li,
.summary-content ol li {
  list-style-type: decimal;
  margin: 0.25em 0;
}

.message-text h1,
.message-text h2,
.message-text h3,
.message-text h4,
.message-text h5,
.message-text h6,
.summary-content h1,
.summary-content h2,
.summary-content h3,
.summary-content h4,
.summary-content h5,
.summary-content h6 {
  margin: 0.75em 0 0.5em 0;
  font-weight: 600;
  line-height: 1.3;
}

.message-text h1,
.summary-content h1 {
  font-size: 1.5em;
}

.message-text h2,
.summary-content h2 {
  font-size: 1.35em;
}

.message-text h3,
.summary-content h3 {
  font-size: 1.25em;
}

.message-text h4,
.summary-content h4 {
  font-size: 1.15em;
}

.message-text code,
.summary-content code {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.message-text pre,
.summary-content pre {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 0.75em;
  border-radius: 5px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.message-text pre code,
.summary-content pre code {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

.message-text a,
.summary-content a {
  color: var(--accent-color);
  text-decoration: none;
}

.message-text a:hover,
.summary-content a:hover {
  text-decoration: underline;
}

.message-text table,
.summary-content table {
  border-collapse: collapse;
  margin: 0.5em 0;
  width: 100%;
}

.message-text table th,
.message-text table td,
.summary-content table th,
.summary-content table td {
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0.5em;
  text-align: left;
}

.message-text table th,
.summary-content table th {
  background-color: rgba(255, 255, 255, 0.1);
}

.chat-input {
  margin-top: auto;
}

.chat-textarea {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 8px 15px;
  background-color: var(--input-bg);
  border-radius: 30px;
  border: 1px solid var(--border-color);
}

.chat-textarea:focus-within {
  border-color: var(--accent-color);
  box-shadow: 0 0 0 1px var(--accent-color);
}

.chat-textarea textarea {
  flex: 1;
  min-height: 40px;
  max-height: 200px;
  overflow-y: auto;
  resize: none;
  padding: 10px 5px;
  background-color: transparent;
  border: none;
  color: var(--text-color);
  font-size: 1rem;
}

.chat-textarea textarea:focus {
  outline: none;
}

.chat-textarea textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-textarea .submit-btn {
  margin-left: 10px;
  height: 40px;
  padding: 8px 15px;
  border-radius: 20px;
  border: none;
  background-color: var(--accent-color);
  color: white;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s ease;
}

.chat-textarea .submit-btn:hover {
  filter: brightness(1.1);
  transform: scale(1.05);
}

.chat-textarea .submit-btn:disabled {
  background-color: #cccccc;
  color: #888888;
  cursor: not-allowed;
  transform: none;
}

.chat-textarea .submit-btn i {
  font-size: 1rem;
  margin-right: 5px;
}

.summary-panel {
  position: relative;
  flex: 1;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  height: calc(100vh - 180px);
  /* 减去进度条、导航栏和padding的高度 */
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.5s ease;
  border: 1px solid var(--border-color);
}

.summary-header {
  padding: 15px;
  border-bottom: 1px solid var(--border-color);
}

.summary-header h3 {
  margin: 0;
  color: var(--accent-color);
  font-size: 1.3rem;
}

.summary-content {
  flex: 1;
  padding: 20px;
  padding-right: 25px;
  /* 增加右侧padding，为滚动条预留空间 */
  overflow-y: scroll;
  /* 改为scroll而不是auto，始终显示滚动条 */
  line-height: 1.6;
  scrollbar-gutter: stable;
  /* 现代浏览器支持的滚动条空间预留属性 */
}

/* 场景名称移至顶部 */
.scenario-name-container {
  padding: 15px;
  margin-bottom: 12px;
  border-bottom: 1px dashed var(--border-color);
}

.scenario-name-container label {
  font-size: 0.9rem;
  margin-bottom: 5px;
  color: var(--text-color);
  display: block;
}

.scenario-name-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 6px;
  border: 1px solid var(--border-color);
  background-color: rgba(255, 255, 255, 0.05);
  color: var(--text-color);
  font-size: 1rem;
  transition: all 0.2s ease;
}

.scenario-name-input:disabled {
  color: #888888;
  cursor: not-allowed;
  transform: none;
}

.scenario-name-input:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 1px var(--accent-color);
}

.name-hint {
  font-size: 0.8rem;
  color: var(--text-color);
  margin-top: 5px;
}

.protocol-section {
  margin-bottom: 20px;
}

.protocol-section h4 {
  color: var(--accent-color);
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.protocol-section ul {
  padding-left: 20px;
}

.protocol-section li {
  margin-bottom: 5px;
  position: relative;
  list-style: none;
  padding-left: 1.2em;
}

.protocol-section ul li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--accent-color);
}

.protocol-section ol li {
  position: relative;
  list-style: none;
  padding-left: 1.5em;
  counter-increment: list-counter;
}

.protocol-section ol li::before {
  content: counter(list-counter) ".";
  position: absolute;
  left: 0;
  color: var(--accent-color);
  font-weight: bold;
}

.model-visual {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 20px 0;
}

.model-node {
  padding: 10px 15px;
  border-radius: 20px;
  display: inline-block;
}

.model-node.primary {
  background-color: var(--accent-color);
  color: white;
}

.model-node.secondary {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
}

.model-connector {
  height: 2px;
  width: 50px;
  background-color: var(--text-color);
  margin: 0 10px;
}

/* 思考中的动画样式 */
.thinking-dots {
  display: flex;
  align-items: center;
  height: 30px;
}

.thinking-dots span {
  width: 8px;
  height: 8px;
  margin: 0 3px;
  background-color: var(--text-color);
  border-radius: 50%;
  display: inline-block;
  animation: pulse 1.5s infinite ease-in-out;
}

.thinking-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.thinking-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulse {

  0%,
  100% {
    transform: scale(1);
    opacity: 0.5;
  }

  50% {
    transform: scale(1.5);
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(50px);
    opacity: 0;
  }

  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.shake {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {

  0%,
  100% {
    transform: translateX(0);
  }

  10%,
  30%,
  50%,
  70%,
  90% {
    transform: translateX(-5px);
  }

  20%,
  40%,
  60%,
  80% {
    transform: translateX(5px);
  }
}

.summary-footer {
  padding: 15px 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
}

.next-btn {
  padding: 12px 24px;
  border-radius: 8px;
  border: none;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: var(--accent-color);
  color: white;
  align-self: flex-end;
}

.next-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: rgba(65, 112, 243, 0.5);
}

.next-btn:hover {
  transform: translateY(-2px);
}

.next-btn i {
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .chat-area {
    flex: 2;
  }
}

@media (max-width: 768px) {
  .chat-mode-layout {
    flex-direction: column;
    padding: 10px;
    min-height: calc(100vh - 160px);
    /* 移动端调整高度 */
  }

  .chat-area {
    padding-right: 0;
    margin-bottom: 20px;
    height: 50vh;
  }

  .summary-panel {
    height: 40vh;
  }

  .model-visual {
    flex-direction: column;
  }

  .model-connector {
    width: 2px;
    height: 20px;
    margin: 10px 0;
  }

  .summary-footer {
    flex-direction: column;
  }

  .next-btn {
    align-self: stretch;
  }
}

.protocol-section .capitalize-text {
  text-transform: capitalize;
}
</style>
