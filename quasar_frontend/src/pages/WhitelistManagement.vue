<template>
  <div class="q-pa-md">
    <div class="text-h4 q-mb-md">Whitelist Management</div>
    <div class="text-subtitle2 q-mb-lg text-grey-7">
      Configure which conditions determine if a domain is accessible or not. 
      Enable/disable conditions or add custom patterns.
    </div>

    <!-- Action Buttons -->
    <div class="q-mb-lg">
      <q-btn 
        color="primary" 
        icon="refresh" 
        label="Refresh Data" 
        @click="refreshData"
        :loading="loading"
        class="q-mr-md"
      />
      <q-btn 
        color="positive" 
        icon="add" 
        label="Add Custom Condition" 
        @click="showAddDialog = true"
        class="q-mr-md"
      />
      <q-btn 
        color="orange" 
        icon="settings" 
        label="Initialize Defaults" 
        @click="initializeDefaults"
        :loading="initLoading"
      />
    </div>

    <!-- Success Conditions Table -->
    <div class="q-mb-xl">
      <div class="text-h5 q-mb-md text-green-7">
        <q-icon name="check_circle" class="q-mr-sm" />
        Success Conditions (Domain Accessible)
      </div>
      <div class="text-caption q-mb-md text-grey-6">
        These patterns indicate a domain is accessible when found in curl results
      </div>
      
      <q-table
        :rows="successConditions"
        :columns="conditionColumns"
        row-key="id"
        :pagination="{ rowsPerPage: 0 }"
        flat
        bordered
        class="q-mb-lg"
      >
        <template v-slot:body-cell-priority="props">
          <q-td :props="props">
            <q-input
              :model-value="props.row.priority"
              @update:model-value="val => updatePriority(props.row, val)"
              type="number"
              dense
              borderless
              input-class="text-center"
              style="width: 60px"
              debounce="500"
            />
          </q-td>
        </template>

        <template v-slot:body-cell-is_enabled="props">
          <q-td :props="props">
            <q-toggle
              :model-value="props.row.is_enabled"
              @update:model-value="toggleCondition(props.row)"
              color="positive"
              :disable="toggleLoading"
            />
          </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <q-btn
              icon="edit"
              color="primary"
              size="sm"
              flat
              round
              @click="editCondition(props.row)"
              class="q-mr-sm"
            />
            <q-btn
              v-if="!props.row.is_built_in"
              icon="delete"
              color="negative"
              size="sm"
              flat
              round
              @click="deleteCondition(props.row)"
            />
          </q-td>
        </template>
      </q-table>
    </div>

    <!-- Failure Conditions Table -->
    <div class="q-mb-xl">
      <div class="text-h5 q-mb-md text-red-7">
        <q-icon name="error" class="q-mr-sm" />
        Failure Conditions (Domain Not Accessible)
      </div>
      <div class="text-caption q-mb-md text-grey-6">
        These patterns indicate a domain is not accessible when found in curl results
      </div>
      
      <q-table
        :rows="failureConditions"
        :columns="conditionColumns"
        row-key="id"
        :pagination="{ rowsPerPage: 0 }"
        flat
        bordered
      >
        <template v-slot:body-cell-priority="props">
          <q-td :props="props">
            <q-input
              :model-value="props.row.priority"
              @update:model-value="val => updatePriority(props.row, val)"
              type="number"
              dense
              borderless
              input-class="text-center"
              style="width: 60px"
              debounce="500"
            />
          </q-td>
        </template>

        <template v-slot:body-cell-is_enabled="props">
          <q-td :props="props">
            <q-toggle
              :model-value="props.row.is_enabled"
              @update:model-value="toggleCondition(props.row)"
              color="negative"
              :disable="toggleLoading"
            />
          </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <q-btn
              icon="edit"
              color="primary"
              size="sm"
              flat
              round
              @click="editCondition(props.row)"
              class="q-mr-sm"
            />
            <q-btn
              v-if="!props.row.is_built_in"
              icon="delete"
              color="negative"
              size="sm"
              flat
              round
              @click="deleteCondition(props.row)"
            />
          </q-td>
        </template>
      </q-table>
    </div>

    <!-- Add/Edit Dialog -->
    <q-dialog v-model="showAddDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section>
          <div class="text-h6">{{ editingCondition ? 'Edit' : 'Add' }} Condition</div>
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveCondition" class="q-gutter-md">
            <q-select
              v-model="formData.condition_type"
              :options="conditionTypeOptions"
              label="Condition Type"
              filled
              emit-value
              map-options
              :disable="editingCondition !== null"
            />

            <q-input
              v-model="formData.condition_name"
              label="Condition Name"
              filled
              required
              :rules="[val => !!val || 'Name is required']"
            />

            <q-input
              v-model="formData.condition_pattern"
              label="Pattern to Match"
              filled
              required
              :rules="[val => !!val || 'Pattern is required']"
              hint="Text pattern that will be searched for in curl results"
            />

            <q-input
              v-model="formData.description"
              label="Description"
              filled
              type="textarea"
              rows="2"
              hint="Describe what this condition does"
            />

            <q-input
              v-model="formData.country_specific"
              label="Country Specific (optional)"
              filled
              hint="Leave empty for all countries, or specify like 'China', 'Korea'"
            />

            <q-input
              v-model.number="formData.priority"
              label="Priority (lower = higher priority)"
              filled
              type="number"
              :rules="[val => val >= 1 || 'Priority must be at least 1']"
              hint="Lower numbers are checked first. Default is 100."
            />

            <q-toggle
              v-model="formData.is_enabled"
              label="Enabled"
              color="positive"
            />
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="closeAddDialog" />
          <q-btn 
            color="primary" 
            label="Save" 
            @click="saveCondition"
            :loading="saveLoading"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <span class="q-ml-sm">
            Are you sure you want to delete the condition "{{ conditionToDelete?.condition_name }}"?
          </span>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" @click="showDeleteDialog = false" />
          <q-btn 
            color="negative" 
            label="Delete" 
            @click="confirmDelete"
            :loading="deleteLoading"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import axios from 'axios'

export default {
  name: 'WhitelistManagement',
  setup() {
    const $q = useQuasar()
    
    // Reactive data
    const conditions = ref([])
    const loading = ref(false)
    const initLoading = ref(false)
    const toggleLoading = ref(false)
    const saveLoading = ref(false)
    const deleteLoading = ref(false)
    
    // Dialog states
    const showAddDialog = ref(false)
    const showDeleteDialog = ref(false)
    const editingCondition = ref(null)
    const conditionToDelete = ref(null)
    
    // Form data
    const formData = ref({
      condition_type: 'success',
      condition_name: '',
      condition_pattern: '',
      description: '',
      country_specific: '',
      priority: 100,
      is_enabled: true
    })

    // Computed properties - sorted by priority (lower = higher priority)
    const successConditions = computed(() =>
      conditions.value
        .filter(c => c.condition_type === 'success')
        .sort((a, b) => (a.priority || 100) - (b.priority || 100))
    )

    const failureConditions = computed(() =>
      conditions.value
        .filter(c => c.condition_type === 'failure')
        .sort((a, b) => (a.priority || 100) - (b.priority || 100))
    )

    // Table columns
    const conditionColumns = [
      {
        name: 'priority',
        required: true,
        label: 'Priority',
        align: 'center',
        field: 'priority',
        sortable: true,
        style: 'width: 80px'
      },
      {
        name: 'condition_name',
        required: true,
        label: 'Name',
        align: 'left',
        field: 'condition_name',
        sortable: true
      },
      {
        name: 'condition_pattern',
        required: true,
        label: 'Pattern',
        align: 'left',
        field: 'condition_pattern',
        sortable: true
      },
      {
        name: 'description',
        label: 'Description',
        align: 'left',
        field: 'description'
      },
      {
        name: 'country_specific',
        label: 'Country',
        align: 'center',
        field: 'country_specific',
        format: (val) => val || 'All'
      },
      {
        name: 'is_built_in',
        label: 'Type',
        align: 'center',
        field: 'is_built_in',
        format: (val) => val ? 'Built-in' : 'Custom'
      },
      {
        name: 'is_enabled',
        label: 'Enabled',
        align: 'center',
        field: 'is_enabled'
      },
      {
        name: 'actions',
        label: 'Actions',
        align: 'center'
      }
    ]

    const conditionTypeOptions = [
      { label: 'Success (Domain Accessible)', value: 'success' },
      { label: 'Failure (Domain Not Accessible)', value: 'failure' }
    ]

    // API Functions
    const fetchConditions = async () => {
      try {
        loading.value = true
        console.log('[WHITELIST MANAGEMENT] 📥 Fetching conditions...')
        
        const response = await axios.get('http://localhost:5030/whitelist/api/whitelist/conditions')
        conditions.value = response.data
        
        console.log(`[WHITELIST MANAGEMENT] ✅ Loaded ${conditions.value.length} conditions`)
      } catch (error) {
        console.error('[WHITELIST MANAGEMENT] ❌ Error fetching conditions:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to load conditions',
          icon: 'error'
        })
      } finally {
        loading.value = false
      }
    }

    const toggleCondition = async (condition) => {
      try {
        toggleLoading.value = true
        console.log(`[WHITELIST MANAGEMENT] 🔄 Toggling condition: ${condition.condition_name}`)
        
        const response = await axios.post(
          `http://localhost:5030/whitelist/api/whitelist/conditions/toggle/${condition.id}`
        )
        
        // Update local data
        const index = conditions.value.findIndex(c => c.id === condition.id)
        if (index !== -1) {
          conditions.value[index] = response.data
        }
        
        const status = response.data.is_enabled ? 'enabled' : 'disabled'
        console.log(`[WHITELIST MANAGEMENT] ✅ Condition ${status}: ${condition.condition_name}`)
        
        $q.notify({
          color: 'positive',
          message: `Condition ${status}: ${condition.condition_name}`,
          icon: 'check'
        })
      } catch (error) {
        console.error('[WHITELIST MANAGEMENT] ❌ Error toggling condition:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to toggle condition',
          icon: 'error'
        })
      } finally {
        toggleLoading.value = false
      }
    }

    const updatePriority = async (condition, newPriority) => {
      const priority = parseInt(newPriority)
      if (isNaN(priority) || priority < 1) return
      if (priority === condition.priority) return

      try {
        console.log(`[WHITELIST MANAGEMENT] 🔢 Updating priority for ${condition.condition_name}: ${condition.priority} → ${priority}`)

        const response = await axios.post(
          'http://localhost:5030/whitelist/api/whitelist/conditions',
          {
            id: condition.id,
            priority: priority
          }
        )

        // Update local data
        const index = conditions.value.findIndex(c => c.id === condition.id)
        if (index !== -1) {
          conditions.value[index] = response.data
        }

        console.log(`[WHITELIST MANAGEMENT] ✅ Priority updated for ${condition.condition_name}`)
        $q.notify({
          color: 'positive',
          message: `Priority updated: ${condition.condition_name} → ${priority}`,
          icon: 'check',
          timeout: 1500
        })
      } catch (error) {
        console.error('[WHITELIST MANAGEMENT] ❌ Error updating priority:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to update priority',
          icon: 'error'
        })
      }
    }

    const saveCondition = async () => {
      try {
        saveLoading.value = true
        console.log('[WHITELIST MANAGEMENT] 💾 Saving condition:', formData.value.condition_name)
        
        const payload = { ...formData.value }
        if (editingCondition.value) {
          payload.id = editingCondition.value.id
        }
        
        const response = await axios.post(
          'http://localhost:5030/whitelist/api/whitelist/conditions',
          payload
        )
        
        if (editingCondition.value) {
          // Update existing condition
          const index = conditions.value.findIndex(c => c.id === editingCondition.value.id)
          if (index !== -1) {
            conditions.value[index] = response.data
          }
          console.log(`[WHITELIST MANAGEMENT] ✏️ Updated condition: ${response.data.condition_name}`)
        } else {
          // Add new condition
          conditions.value.push(response.data)
          console.log(`[WHITELIST MANAGEMENT] ➕ Added condition: ${response.data.condition_name}`)
        }
        
        $q.notify({
          color: 'positive',
          message: `Condition ${editingCondition.value ? 'updated' : 'added'} successfully`,
          icon: 'check'
        })
        
        closeAddDialog()
      } catch (error) {
        console.error('[WHITELIST MANAGEMENT] ❌ Error saving condition:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to save condition',
          icon: 'error'
        })
      } finally {
        saveLoading.value = false
      }
    }

    const editCondition = (condition) => {
      editingCondition.value = condition
      formData.value = {
        condition_type: condition.condition_type,
        condition_name: condition.condition_name,
        condition_pattern: condition.condition_pattern,
        description: condition.description,
        country_specific: condition.country_specific || '',
        priority: condition.priority || 100,
        is_enabled: condition.is_enabled
      }
      showAddDialog.value = true
    }

    const deleteCondition = (condition) => {
      conditionToDelete.value = condition
      showDeleteDialog.value = true
    }

    const confirmDelete = async () => {
      try {
        deleteLoading.value = true
        console.log(`[WHITELIST MANAGEMENT] 🗑️ Deleting condition: ${conditionToDelete.value.condition_name}`)
        
        await axios.delete(
          `http://localhost:5030/whitelist/api/whitelist/conditions/${conditionToDelete.value.id}`
        )
        
        // Remove from local data
        const index = conditions.value.findIndex(c => c.id === conditionToDelete.value.id)
        if (index !== -1) {
          conditions.value.splice(index, 1)
        }
        
        console.log(`[WHITELIST MANAGEMENT] ✅ Deleted condition: ${conditionToDelete.value.condition_name}`)
        $q.notify({
          color: 'positive',
          message: `Deleted condition: ${conditionToDelete.value.condition_name}`,
          icon: 'check'
        })
        
        showDeleteDialog.value = false
        conditionToDelete.value = null
      } catch (error) {
        console.error('[WHITELIST MANAGEMENT] ❌ Error deleting condition:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to delete condition',
          icon: 'error'
        })
      } finally {
        deleteLoading.value = false
      }
    }

    const initializeDefaults = async () => {
      try {
        initLoading.value = true
        console.log('[WHITELIST MANAGEMENT] 🎯 Initializing default conditions...')
        
        const response = await axios.post('http://localhost:5030/whitelist/api/whitelist/initialize')
        
        console.log('[WHITELIST MANAGEMENT] ✅ Default conditions initialized')
        $q.notify({
          color: 'positive',
          message: response.data.message,
          icon: 'check'
        })
        
        // Refresh conditions
        await fetchConditions()
      } catch (error) {
        console.error('[WHITELIST MANAGEMENT] ❌ Error initializing defaults:', error)
        $q.notify({
          color: 'negative',
          message: 'Failed to initialize default conditions',
          icon: 'error'
        })
      } finally {
        initLoading.value = false
      }
    }

    const refreshData = () => {
      fetchConditions()
    }

    const closeAddDialog = () => {
      showAddDialog.value = false
      editingCondition.value = null
      formData.value = {
        condition_type: 'success',
        condition_name: '',
        condition_pattern: '',
        description: '',
        country_specific: '',
        priority: 100,
        is_enabled: true
      }
    }

    // Lifecycle
    onMounted(() => {
      console.log('[WHITELIST MANAGEMENT] 🚀 Component mounted')
      fetchConditions()
    })

    return {
      // Data
      conditions,
      successConditions,
      failureConditions,
      loading,
      initLoading,
      toggleLoading,
      saveLoading,
      deleteLoading,
      
      // Dialog states
      showAddDialog,
      showDeleteDialog,
      editingCondition,
      conditionToDelete,
      
      // Form
      formData,
      conditionTypeOptions,
      
      // Table
      conditionColumns,
      
      // Methods
      fetchConditions,
      toggleCondition,
      updatePriority,
      saveCondition,
      editCondition,
      deleteCondition,
      confirmDelete,
      initializeDefaults,
      refreshData,
      closeAddDialog
    }
  }
}
</script>