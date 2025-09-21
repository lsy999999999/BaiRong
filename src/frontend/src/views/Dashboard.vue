<template>
  <div class="dashboard-layout">
    <Sidebar ref="sidebar" />

    <div class="main-content">
      <div class="header">
        <!-- <h1 class="title">AI Social Behavior Simulator</h1> -->
      </div>

      <div class="search-container">
        <div class="guide-text">
          <p>
            Describe the social scenario you'd like to simulate in natural language
          </p>
        </div>

        <div class="search-box">
          <div class="textarea-container">
            <textarea
              v-model="queryInput"
              placeholder="Example: 'Simulate the initial interaction between two strangers in a public place...'"
              rows="5"
              @keyup.ctrl.enter="handleSubmit"
            ></textarea>
            <div class="textarea-actions">
              <div class="model-selection">
                <label for="model-select">The LLM used for scenario construction</label>
                <select
                  id="model-select"
                  v-model="selectedModel"
                  @change="handleModelChange"
                >
                  <option v-for="model in models" :key="model" :value="model.value">
                    {{ model.name }}
                  </option>
                </select>
              </div>
              <button class="submit-btn" @click="handleSubmit">
                <i class="fa fa-arrow-right"></i> Send
              </button>
            </div>
          </div>
        </div>
<!-- 
        <div class="examples">
          <h3>Sample descriptions:</h3>
          <div class="example-items">
            <div
              v-for="(example, index) in exampleQuestions"
              :key="index"
              class="example"
              @click="setExample(example)"
              :class="{ clicked: clickedExample === index }"
            >
              {{ example }}
            </div>
          </div>
        </div> -->
      </div>

      <div class="result-container" v-if="showResults">
        <h2>Simulation Results</h2>
        <div class="result-content" v-html="resultContent"></div>
        <button class="new-query-btn" @click="resetSearch">New Question</button>
      </div>

      <footer>
        <p>RUC YuLan Team</p>
      </footer>
    </div>
  </div>
</template>

<script>
import Sidebar from "../components/Sidebar.vue";
import axios from "axios";

import { ElMessageBox, ElMessage } from "element-plus";
export default {
  name: "Dashboard",
  components: {
    Sidebar,
  },
  data() {
    return {
      queryInput: "",
      selectedModel: "",
      modelItem: {},
      showResults: false,
      resultContent: "",
      clickedExample: null,
      exampleQuestions: [
        "Simulate a conversation between an interviewer and a job applicant",
        "Analyze behavioral changes of team members under project pressure",
        "Simulate interactions between people of different cultural backgrounds in a restaurant",
        "Analyze the pathways and influencing factors of information spread on social media",
      ],
      models: [], // 存储从接口获取的模型列表
    };
  },
  mounted() {
    this.fetchModels();
    this.getExamples();
  },
  methods: {
    /**获取示例问题 */
    getExamples() {
      axios.get("/api/odd/examples").then((response) => {
        if (Array.isArray(response.data)){
          this.exampleQuestions = response.data;
        }else{
          ElMessageBox.confirm(
            "The data could not be fetched. Would you like to try again?",
            "Notice",
            {
              confirmButtonText: "OK",
              cancelButtonText: "Cancel",
              type: "warning"
            }
          ).then(() => {
            // 确认后返回仪表盘页面
            this.getExamples();
          }).catch(() => {
            // 取消后也返回仪表盘页面，因为没有查询内容无法继续
            this.$router.push('/');
          });
        }
      });
    },
    /**模型选择（如果models不为空，设置第一个模型为默认选择） */
    handleModelChange() {
      this.modelItem = {};
      for (let i in this.models) {
        if (this.selectedModel == this.models[i].value) {
          this.modelItem = this.models[i];
        }
      }
    },
    /**获取模型列表 */
    fetchModels() {
      axios
        .get("/api/config/models",{
          params: {
            category: "chat"
          }
        })
        .then((response) => {
          for (let i in response.data.models) {
            for (let j in response.data.models[i]) {
              let item = response.data.models[i][j];
              this.models.push({
                value: item,
                name: item,
                category: i,
              });
            }
          }
          // 如果models不为空，设置第一个模型为默认选择
          if (this.models.length > 0) {
            this.selectedModel = this.models[0].value;
            this.handleModelChange();
          }
        })
        .catch((error) => {
          console.error("获取模型列表失败:", error);
        });
    },
    /**提交查询 */
    handleSubmit() {
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

      ElMessageBox.confirm(
        "Are you sure you want to proceed to the next step?",
        "Confirmation",
        {
          confirmButtonText: "OK",
          cancelButtonText: "Cancel",
        }
      ).then(() => {
        // 清空原有缓存数据
        window.summaryContent = null;
        window.messages = null;
        // 删除场景名称
        localStorage.removeItem("scenarioName");
        // 通过window全局变量传递查询参数，而不是通过URL
        window.query = query;
        // 跳转到聊天模式页面，只传递模型和类别参数
        this.$router.push({
          path: "/simulation",
          query: {
            model_name: this.modelItem.value,
            category: this.modelItem.category,
            step: 1,
          },
        });
      });
    },
    /**设置示例问题 */
    setExample(example) {
      this.queryInput = example;
      this.clickedExample = this.exampleQuestions.indexOf(example);

      setTimeout(() => {
        this.clickedExample = null;
      }, 300);
    },
    resetSearch() {
      this.showResults = false;
      this.queryInput = "";
      this.resultContent = "";

      // Scroll back to search
      this.$nextTick(() => {
        const searchBox = this.$el.querySelector(".search-box");
        if (searchBox) {
          searchBox.scrollIntoView({
            behavior: "smooth",
          });
        }
      });
    },
    /**生成加载动画 */
    generateLoadingHTML() {
      return `
        <div class="loading-container">
          <div class="loading-animation">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
          <p>AI is thinking...</p>
        </div>
      `;
    },
    /**生成模拟响应 */
    generateMockResponse(query) {
      // Return appropriate mock response based on query
      if (query.includes("interview") || query.includes("job applicant")) {
        return this.generateInterviewScenario();
      } else if (query.includes("team") || query.includes("pressure")) {
        return this.generateTeamPressureScenario();
      } else if (query.includes("cultural") || query.includes("restaurant")) {
        return this.generateCulturalScenario();
      } else if (query.includes("social media") || query.includes("information")) {
        return this.generateSocialMediaScenario();
      } else {
        return this.generateDefaultScenario(query);
      }
    },
    /**生成面试场景 */
    generateInterviewScenario() {
      return `
        <h3>Simulation Scenario: Interviewer and Job Applicant Conversation</h3>
        <div class="scenario-content">
          <p><strong>Background:</strong> Product Manager position interview at a tech company</p>
          <p><strong>Participants:</strong> Interviewer (Senior Product Director), Applicant (Product Manager with 3 years experience)</p>
          
          <div class="conversation">
            <div class="message interviewer">
              <div class="avatar">Interviewer</div>
              <div class="text">Hello, nice to meet you. Please briefly introduce your previous work experience and the main product projects you were responsible for.</div>
            </div>
            
            <div class="message candidate">
              <div class="avatar">Applicant</div>
              <div class="text">Hello, thank you for this interview opportunity. I have 3 years of experience as a product manager, previously responsible for optimizing mobile payment products at Company A. Our team successfully increased payment conversion rate by 15% and reduced user complaints by 23%...</div>
            </div>
            
            <div class="message interviewer">
              <div class="avatar">Interviewer</div>
              <div class="text">Sounds great. Can you specifically talk about what strategies you employed in resolving user complaints? Especially when facing conflicts between the technical team and business requirements, how did you balance them?</div>
            </div>
            
            <div class="message candidate">
              <div class="avatar">Applicant</div>
              <div class="text">Certainly. I first conducted a systematic analysis of complaint reasons and found that 80% of the issues were centered on complex payment processes and timeout failures...</div>
            </div>
          </div>
          
          <div class="analysis">
            <h4>Behavioral Analysis:</h4>
            <ul>
              <li>The interviewer establishes a comfortable dialogue environment through open-ended questions while assessing the applicant's communication skills</li>
              <li>The applicant uses data to support their achievements, demonstrating a results-oriented work approach</li>
              <li>The interviewer's follow-up questions demonstrate a focus on practical problem-solving abilities rather than just surface-level achievements</li>
              <li>The entire conversation illustrates information exchange patterns and implicit evaluation processes in professional settings</li>
            </ul>
          </div>
        </div>
      `;
    },
    /**生成团队压力场景 */
    generateTeamPressureScenario() {
      return `
        <h3>Simulation Scenario: Team Behavior Changes Under Project Pressure</h3>
        <div class="scenario-content">
          <p><strong>Background:</strong> Software development team facing deadline pressure before product release</p>
          <p><strong>Team Composition:</strong> Project Manager, 3 Developers, 1 Designer, 1 QA Tester</p>
          
          <div class="phases">
            <div class="phase">
              <h4>Phase One: Initial Pressure Awareness (2 weeks before deadline)</h4>
              <ul>
                <li>Team members begin extending working hours, proactively working overtime</li>
                <li>Communication frequency increases while maintaining structured meeting formats</li>
                <li>Project manager increases progress check frequency, begins identifying potential risk points</li>
                <li>Team atmosphere slightly tense, but generally maintains a positive mindset</li>
              </ul>
            </div>
            
            <div class="phase">
              <h4>Phase Two: Intensified Pressure (1 week before deadline)</h4>
              <ul>
                <li>Team communication shifts from formal to informal, with significant increase in instant messaging usage</li>
                <li>First role conflict emerges: development team and QA team disagree on bug priority</li>
                <li>Designer begins simplifying visual elements to meet time requirements</li>
                <li>Project manager starts reprioritizing tasks, postponing some features to the next version</li>
              </ul>
            </div>
            
            <div class="phase">
              <h4>Phase Three: High Pressure Period (final 72 hours)</h4>
              <ul>
                <li>Team members show obvious stress reactions: reduced sleep, increased emotional fluctuations</li>
                <li>Team divides into two coping patterns: some members become unusually focused, others show attention dispersion</li>
                <li>Decision-making process simplified, project manager's authority concentration increases</li>
                <li>Mutual assistance increases among team members, experienced members proactively help newcomers</li>
              </ul>
            </div>
          </div>
          
          <div class="analysis">
            <h4>Behavioral Analysis:</h4>
            <p>This simulation demonstrates several key behavioral patterns of teams under pressure:</p>
            <ol>
              <li>Communication patterns shift from structured to unstructured</li>
              <li>Decision chains shorten under pressure, with clear hierarchy</li>
              <li>Individual differences are amplified in high-pressure environments</li>
              <li>Team cohesion is challenged but also reinforced simultaneously</li>
              <li>Goal reprioritization is a key adaptation mechanism for time pressure</li>
            </ol>
          </div>
        </div>
      `;
    },
    /**生成文化差异场景 */
    generateCulturalScenario() {
      return `
        <h3>Simulation Scenario: Interactions Among People of Different Cultural Backgrounds in a Restaurant</h3>
        <div class="scenario-content">
          <p><strong>Background:</strong> International business dinner, business partners from different cultural backgrounds dining together</p>
          <p><strong>Participants:</strong> Business representatives from China, United States, Japan, and Germany</p>
          
          <div class="cultural-interactions">
            <div class="interaction">
              <h4>Seating and Greeting Phase</h4>
              <ul>
                <li>Chinese representative waits for elders and higher-ranking individuals to be seated first, showing respect for hierarchy</li>
                <li>American representative proactively introduces themselves and initiates topics, demonstrating a preference for direct communication</li>
                <li>Japanese representative hands business cards using both hands with a slight bow, emphasizing the importance of etiquette</li>
                <li>German representative arrives punctually and expects to start on schedule, reflecting strict time management culture</li>
              </ul>
            </div>
          </div>
          
          <div class="analysis">
            <h4>Behavioral Analysis:</h4>
            <p>This simulation demonstrates key patterns in cross-cultural communication:</p>
            <ol>
              <li>High-context cultures (China, Japan) versus low-context cultures (USA, Germany) communication differences</li>
              <li>Collectivist versus individualist values as expressed in social behaviors</li>
              <li>Power distance perception differences influencing interaction etiquette</li>
            </ol>
          </div>
        </div>
      `;
    },
    /**生成社交媒体场景 */
    generateSocialMediaScenario() {
      return `
        <h3>Simulation Scenario: Pathways and Influencing Factors of Information Spread on Social Media</h3>
        <div class="scenario-content">
          <p><strong>Background:</strong> The spread process of information about a new technology product release on social media platforms</p>
          <p><strong>Initial Information Source:</strong> New product announcement from the tech company's official account</p>
          
          <div class="propagation-phases">
            <div class="phase">
              <h4>Phase One: Initial Spread (0-2 hours)</h4>
              <ul>
                <li>Core fan group (about 20,000 users) receives information, interaction rate around 15%</li>
                <li>Tech bloggers and KOLs begin forwarding with personal comments, adding an information interpretation layer</li>
                <li>Information primarily spreads within vertical domains, with professional user groups as main recipients</li>
              </ul>
            </div>
          </div>
          
          <div class="analysis">
            <h4>Behavioral Analysis:</h4>
            <p>This simulation reveals several key behavioral patterns in social media information spread:</p>
            <ol>
              <li>Information spread follows "small-world network" theory, with key nodes (KOLs) acting as accelerators in dissemination</li>
              <li>Information undergoes "mutation" and "evolution" during spread, gradually deviating from original content</li>
            </ol>
          </div>
        </div>
      `;
    },
    /**生成默认场景 */
    generateDefaultScenario(query) {
      return `
        <h3>Simulation Scenario: ${query}</h3>
        <div class="scenario-content">
          <p><strong>Background:</strong> Social behavior simulation scenario created based on your request</p>
          
          <div class="simulation">
            <p>AI has received your request and will generate a detailed social behavior simulation analysis based on this scenario. In actual applications,
            the system would analyze the following elements in similar scenarios:</p>
            
            <ul>
              <li>Role positioning and power relationships of participants</li>
              <li>Communication patterns and non-verbal cues in interaction processes</li>
              <li>Influence of social norms and implicit rules</li>
              <li>Individual decision processes and group dynamics</li>
              <li>Constraint effects of situational factors on behavioral choices</li>
              <li>Behavioral variations produced by cultural background differences</li>
            </ul>
            
            <p>A complete analysis would include scenario recreation, behavioral sequences, motivation analysis, outcome prediction, and variable control suggestions.</p>
          </div>
          
          <div class="analysis">
            <h4>Application Value of Such Simulations:</h4>
            <ol>
              <li>Help AI systems learn complex human social interaction patterns</li>
              <li>Provide controllable experimental scenarios for social science research</li>
              <li>Train intelligent agents' decision-making abilities in specific social environments</li>
              <li>Assist in developing human-machine interaction modes that better meet human expectations</li>
              <li>Provide predictive guidance for cross-cultural communication and organizational management</li>
            </ol>
          </div>
        </div>
      `;
    },
  },
};
</script>

<style scoped>
.dashboard-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  margin-left: 320px;
  padding-top: 40px;
  height: 100vh;
  display: flex;
  align-items: center;
  /* flex-direction: column; */
  overflow-y: auto;
  position: relative;
}

.header {
  text-align: center;
  margin-bottom: 30px;
  animation: fadeIn 1s ease;
}

.header h1 {
  font-size: 2.8rem;
  color: var(--text-color);
  margin-bottom: 10px;
}

.subtitle {
  font-size: 1.2rem;
  color: var(--secondary-color);
  max-width: 600px;
  margin: 0 auto;
}

.search-container {
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px auto;
  animation: slideUp 0.8s ease;
}

.guide-text {
  width: 100%;
  text-align: center;
  margin-bottom: 20px;
  font-size: 1.1rem;
  color: var(--secondary-color);
}

.search-box {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  margin-bottom: 30px;
  padding: 0 25px;
}

.model-selection {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.model-selection label {
  font-size: 1rem;
  margin-right: 10px;
  color: var(--text-color);
}

.model-selection select {
  padding: 8px 12px;
  border-radius: 6px;
  background-color: var(--input-bg);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  font-size: 0.95rem;
  cursor: pointer;
  outline: none;
  transition: all 0.2s ease;
}

.model-selection select:focus {
  border-color: var(--accent-color);
}

.light-theme .model-selection select {
  background-color: white;
  border-color: #ddd;
}

.light-theme .model-selection select:hover {
  border-color: #aaa;
}

.textarea-container {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--input-bg);
  border-radius: 15px;
  box-shadow: var(--box-shadow);
  transition: box-shadow 0.3s ease;
}

.textarea-container:focus-within {
  box-shadow: 0 0 0 2px var(--accent-color);
}

.search-box textarea {
  width: 100%;
  padding: 20px 25px;
  border-radius: 15px 15px 0 0;
  border: none;
  background-color: transparent;
  color: var(--text-color);
  font-size: 1.1rem;
  resize: none;
  min-height: 120px;
  max-height: 200px;
  overflow-y: auto;
}

.search-box textarea:focus {
  outline: none;
}

.textarea-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 15px;
  border-top: 1px solid var(--border-color);
  border-radius: 0 0 15px 15px;
}

.action-hint {
  font-size: 0.8rem;
  color: var(--secondary-color);
}

.submit-btn {
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

.submit-btn:hover {
  filter: brightness(1.1);
  transform: scale(1.05);
}

.submit-btn i {
  font-size: 1rem;
  margin-right: 5px;
}

.examples {
  width: 100%;
  margin-top: 10px;
}

.examples h3 {
  text-align: center;
  margin-bottom: 15px;
  color: var(--secondary-color);
  font-weight: 500;
}

.example-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 15px;
}

.example {
  background-color: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.light-theme .example {
  background-color: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.example:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
  border-color: var(--accent-color);
}

.example.clicked {
  background-color: var(--accent-color);
  transform: scale(0.98);
}

.result-container {
  width: 100%;
  max-width: 800px;
  margin: 30px auto;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 30px;
  animation: fadeIn 0.5s ease;
  box-shadow: var(--box-shadow);
}

.result-container h2 {
  margin-bottom: 20px;
  color: var(--accent-color);
}

.result-content {
  line-height: 1.6;
  margin-bottom: 25px;
}

.new-query-btn {
  background-color: var(--secondary-color);
  color: var(--text-color);
  border: none;
  padding: 12px 25px;
  border-radius: 30px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.new-query-btn:hover {
  background-color: var(--accent-color);
}

footer {
  width: 100%;
  margin-top: auto;
  text-align: center;
  color: var(--secondary-color);
  font-size: 0.9rem;
  padding: 20px 0;
  position: absolute;
  bottom: 20px;
}

/* Loading animation styles */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 30px 0;
}

.loading-animation {
  display: flex;
  justify-content: center;
  margin-bottom: 15px;
}

.dot {
  width: 12px;
  height: 12px;
  margin: 0 5px;
  background-color: var(--accent-color);
  border-radius: 50%;
  animation: bounce 1.5s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-15px);
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

/* Conversation styles */
.conversation {
  margin: 20px 0;
  border-left: 3px solid var(--accent-color);
  padding-left: 15px;
}

.message {
  margin-bottom: 15px;
  display: flex;
}

.avatar {
  min-width: 70px;
  font-weight: bold;
  color: var(--accent-color);
}

.text {
  padding: 10px 15px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.05);
}

.interviewer .text {
  border-left: 2px solid #8a2be2;
}

.candidate .text {
  border-left: 2px solid #4682b4;
}

/* Phase analysis styles */
.phases .phase,
.cultural-interactions .interaction,
.propagation-phases .phase {
  margin-bottom: 20px;
  padding: 15px;
  background-color: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.phases h4,
.cultural-interactions h4,
.propagation-phases h4 {
  color: var(--accent-color);
  margin-bottom: 10px;
}

.analysis {
  margin-top: 30px;
  padding: 20px;
  background-color: rgba(138, 43, 226, 0.1);
  border-radius: 10px;
}

.analysis h4 {
  color: var(--accent-color);
  margin-bottom: 15px;
}

/* Responsive design */
@media (max-width: 1024px) {
  .main-content {
    margin-left: 280px;
    padding: 30px;
  }

  .header h1 {
    font-size: 2.4rem;
  }

  .search-box textarea {
    min-height: 100px;
  }
}

@media (max-width: 768px) {
  .dashboard-layout {
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  .main-content {
    margin-left: 0;
    padding: 20px;
    order: 1;
    height: 100vh;
    overflow-y: auto;
  }

  .header h1 {
    font-size: 2.2rem;
  }

  .subtitle {
    font-size: 1rem;
  }

  .example-items {
    grid-template-columns: 1fr;
  }

  .search-box textarea {
    padding: 15px 20px;
    font-size: 1rem;
    min-height: 80px;
  }

  .action-hint {
    display: none;
  }

  .submit-btn {
    padding: 6px 12px;
    font-size: 0.9rem;
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
</style>
