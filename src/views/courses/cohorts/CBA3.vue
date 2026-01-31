<script setup lang="ts">
import { onMounted } from 'vue'
import { CircleCheckIcon, CircleHelpIcon, CircleIcon } from 'lucide-vue-next'
import Button from '@/components/ui/button/Button.vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from '@/components/ui/navigation-menu'
// eslint-disable-next-line import/no-named-default
import { default as ListItem } from '@/components/ui/navigation-menu/NavigationMenuItem.vue'
import router from '@/router'

</script>

<template>
  <div class="flex justify-center px-8 py-16">
    <Card class="w-full max-w-4xl">
      <CardHeader class="gap-4">
        <CardTitle>Teacher Led Cohorts</CardTitle>
        <CardDescription class="mt-4">
          Welcome to the Teacher Led Cohorts. Please choose which Cohort you are enrolled in to get started.
        </CardDescription>
      </CardHeader>
    </Card>
  </div>
</template>

