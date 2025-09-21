<template>
  <div class="event-panel">
    <!-- <h2>Event List</h2> -->

    <div class="search-bar">
      <el-input v-model="searchQuery" placeholder="Search events..." clearable>
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <el-table
      :data="paginatedEvents"
      style="width: 100%"
      border
      stripe
      class="event-table"
    >
      <el-table-column prop="event_type" label="Event Type" width="180" />
      <el-table-column label="Source" width="150">
        <template #default="scope">
          <span v-if="scope.row.source_id === 'ENV'" class="env-source">System Environment</span>
          <el-button v-else type="text" @click="viewAgent(scope.row.source_id)">
            {{ getAgentName(scope.row.source_id) }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column label="Target" width="150">
        <template #default="scope">
          <el-button type="text" @click="viewAgent(scope.row.target_id)">
            {{ getAgentName(scope.row.target_id) }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="step" label="Step" width="80" />
      <el-table-column label="Timestamp" width="180">
        <template #default="scope">
          {{ formatTimestamp(scope.row.timestamp) }}
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="100">
        <template #default="scope">
          <el-button size="small" @click="viewEvent(scope.row)">View</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[10, 20, 30, 50]"
      layout="total, sizes, prev, pager, next, jumper"
      :total="filteredEvents.length"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
      class="pagination"
    />

    <!-- Event Details Dialog -->
    <el-dialog
      v-model="eventDialogVisible"
      title="Event Details"
      width="60%"
      :close-on-click-modal="false"
    >
      <div v-if="selectedEvent" class="event-detail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Event Type">{{
            selectedEvent.event_type
          }}</el-descriptions-item>
          <el-descriptions-item label="Source">
            <span v-if="selectedEvent.source_id === 'ENV'" class="env-source"
              >System Environment</span
            >
            <el-button
              v-else
              type="text"
              @click="
                viewAgent(selectedEvent.source_id);
                eventDialogVisible = false;
              "
            >
              {{ getAgentName(selectedEvent.source_id) }}
            </el-button>
          </el-descriptions-item>
          <el-descriptions-item label="Target">
            <el-button
              type="text"
              @click="
                viewAgent(selectedEvent.target_id);
                eventDialogVisible = false;
              "
            >
              {{ getAgentName(selectedEvent.target_id) }}
            </el-button>
          </el-descriptions-item>
          <el-descriptions-item label="Step">{{
            selectedEvent.step
          }}</el-descriptions-item>
          <el-descriptions-item label="Timestamp">{{
            formatTimestamp(selectedEvent.timestamp)
          }}</el-descriptions-item>

          <!-- Data display for InformationGeneratedEvent -->
          <template
            v-if="
              selectedEvent.event_type === 'InformationGeneratedEvent' &&
              selectedEvent.data
            "
          >
            <el-descriptions-item label="Topic">{{
              selectedEvent.data.topic
            }}</el-descriptions-item>
            <el-descriptions-item label="Content">{{
              selectedEvent.data.content
            }}</el-descriptions-item>
            <el-descriptions-item
              label="Target Opinion Leaders"
              v-if="selectedEvent.data.target_opinion_leaders"
            >
              <div class="target-leaders">
                <el-tag
                  v-for="leaderId in selectedEvent.data.target_opinion_leaders"
                  :key="leaderId"
                  @click="
                    viewAgent(leaderId.toString());
                    eventDialogVisible = false;
                  "
                  class="leader-tag"
                >
                  {{ getAgentName(leaderId.toString()) }}
                </el-tag>
              </div>
            </el-descriptions-item>
          </template>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from "vue";
import { Search } from "@element-plus/icons-vue";
import { useGameStore } from "../../../stores/gameStore";
import { useRouter, useRoute } from "vue-router";
import axios from "axios";

export default {
  name: "EventPanel",
  components: {
    Search,
  },
  setup() {
    const route = useRoute();

    const gameStore = useGameStore();
    const router = useRouter();

    // Get event data from store
    const events = computed(() => gameStore.getEventsData || []);
    const searchQuery = ref("");
    const currentPage = ref(1);
    const pageSize = ref(10);
    const eventDialogVisible = ref(false);
    const selectedEvent = ref(null);

    // Computed property: filtered event list
    const filteredEvents = computed(() => {
      let filtered = !searchQuery.value 
        ? [...events.value] 
        : events.value.filter((event) => {
            const sourceName = getAgentName(event.source_id);
            const targetName = getAgentName(event.target_id);
            const searchLower = searchQuery.value.toLowerCase();

            return (
              event.event_type.toLowerCase().includes(searchLower) ||
              sourceName.toLowerCase().includes(searchLower) ||
              targetName.toLowerCase().includes(searchLower) ||
              (event.data &&
                event.data.topic &&
                event.data.topic.toLowerCase().includes(searchLower)) ||
              (event.data &&
                event.data.content &&
                event.data.content.toLowerCase().includes(searchLower))
            );
          });
      // Sort by timestamp in descending order, latest events shown first
      return filtered.sort((a, b) => b.timestamp - a.timestamp);
    });

    // Paginated event list
    const paginatedEvents = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      return filteredEvents.value.slice(start, end);
    });

    // Method to get agent name
    const getAgentName = (id) => {
      if (id === "ENV") return "System Environment";

      const agents = gameStore.getAgentsData.agents || [];
      const agent = agents.find((a) => a.id === id.toString());

      if (agent && agent.profile && agent.profile.name) {
        return agent.profile.name;
      } else {
        return `Unknown Agent(ID:${id})`;
      }
    };

    // Format timestamp
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return "Unknown time";

      const date = new Date(timestamp * 1000);
      return date.toLocaleString("en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    };

    // View event details
    const viewEvent = (event) => {
      selectedEvent.value = event;
      eventDialogVisible.value = true;
    };

    // View agent details
    const viewAgent = (id) => {
      if (id === "ENV") return; // System Environment cannot be clicked to view

      console.log("View agent:", id);
      // Use the same navigation logic as CharacterPanel, but default to event history tab
      router.replace({
        query: {
          panel: "characterDetail",
          id: id.toString(),
          tab: "history", // Directly show event history tab
        },
      });
    };

    // Handle page size change
    const handleSizeChange = (val) => {
      pageSize.value = val;
      currentPage.value = 1; // Reset to first page
    };

    // Handle page number change
    const handleCurrentChange = (val) => {
      currentPage.value = val;
    };

    return {
      events,
      searchQuery,
      currentPage,
      pageSize,
      eventDialogVisible,
      selectedEvent,
      filteredEvents,
      paginatedEvents,
      getAgentName,
      formatTimestamp,
      handleSizeChange,
      handleCurrentChange,
      viewEvent,
      viewAgent,
    };
  },
};
</script>

<style scoped>
.event-panel {
  /* padding: 20px; */
  height: 100%;
  overflow-y: auto;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-bar .el-input {
  width: 100%;
}

.event-table {
  margin-bottom: 20px;
}

h2 {
  margin-bottom: 20px;
  color: var(--text-color);
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.event-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.env-source {
  color: #909399;
}

.target-leaders {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.leader-tag {
  cursor: pointer;
}
</style>
