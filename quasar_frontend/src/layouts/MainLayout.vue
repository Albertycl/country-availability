<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
        />
        
        <q-toolbar-title> Country Availability </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      bordered
    >
      <q-list>
        <q-item-label header>Navigation</q-item-label>

        <q-item
          clickable
          v-ripple
          :to="'/filtered'"
          exact
        >
          <q-item-section avatar>
            <q-icon name="filter_list" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Filtered Results</q-item-label>
            <q-item-label caption>Success-first whitelist logic, unknown excluded</q-item-label>
          </q-item-section>
        </q-item>

        <q-item
          clickable
          v-ripple
          :to="'/whitelist'"
        >
          <q-item-section avatar>
            <q-icon name="rule" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Whitelist Management</q-item-label>
            <q-item-label caption>Configure success/failure conditions</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { defineComponent, ref } from "vue";

export default defineComponent({
  name: "MainLayout",

  components: {},

  setup() {
    const leftDrawerOpen = ref(false);

    return {
      leftDrawerOpen,
      toggleLeftDrawer() {
        leftDrawerOpen.value = !leftDrawerOpen.value;
      },
    };
  },
});
</script>
