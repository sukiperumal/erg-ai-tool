<script setup lang="ts">
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

const components: { title: string, href: string, description: string }[] = [
  {
    title: 'Alert Dialog',
    href: '/docs/primitives/alert-dialog',
    description:
      'A modal dialog that interrupts the user with important content and expects a response.',
  },
  {
    title: 'Hover Card',
    href: '/docs/primitives/hover-card',
    description:
      'For sighted users to preview content available behind a link.',
  },
  {
    title: 'Progress',
    href: '/docs/primitives/progress',
    description:
      'Displays an indicator showing the completion progress of a task, typically displayed as a progress bar.',
  },
  {
    title: 'Scroll-area',
    href: '/docs/primitives/scroll-area',
    description: 'Visually or semantically separates content.',
  },
  {
    title: 'Tabs',
    href: '/docs/primitives/tabs',
    description:
      'A set of layered sections of content—known as tab panels—that are displayed one at a time.',
  },
  {
    title: 'Tooltip',
    href: '/docs/primitives/tooltip',
    description:
      'A popup that displays information related to an element when the element receives keyboard focus or the mouse hovers over it.',
  },
]

function onClick(cohortId: number) {
  if (cohortId === 1) {
    router.push('/courses/1/cohorts/1')
  } else if (cohortId === 2) {
    router.push('/courses/1/cohorts/2')
  } else if (cohortId === 3) {
    router.push('/courses/1/cohorts/3')
  }
}
</script>

<template>
  <div>
    <div class="flex justify-center py-2">
      <NavigationMenu :viewport="false">
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuTrigger>Home</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul class="grid gap-2 md:w-[400px] lg:w-[500px] lg:grid-cols-[.75fr_1fr]">
                <li class="row-span-3">
                  <NavigationMenuLink as-child>
                    <a
                      class="from-muted/50 to-muted flex h-full w-full flex-col justify-end rounded-md bg-linear-to-b p-6 no-underline outline-hidden select-none focus:shadow-md"
                      href="/"
                    >
                      <div class="mt-4 mb-2 text-lg font-medium">
                        shadcn/ui
                      </div>
                      <p class="text-muted-foreground text-sm leading-tight">
                        Beautifully designed components built with Tailwind CSS.
                      </p>
                    </a>
                  </NavigationMenuLink>
                </li>
                <ListItem to="/docs" title="Introduction">
                  Re-usable components built using Radix UI and Tailwind CSS.
                </ListItem>
                <ListItem to="/docs/installation" title="Installation">
                  How to install dependencies and structure your app.
                </ListItem>
                <ListItem to="/docs/primitives/typography" title="Typography">
                  Styles for headings, paragraphs, lists...etc
                </ListItem>
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuTrigger>Components</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul class="grid w-[400px] gap-2 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                <ListItem
                  v-for="component in components"
                  :key="component.title"
                  :title="component.title"
                  :to="component.href"
                >
                  {{ component.description }}
                </ListItem>
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuLink as-child :class="navigationMenuTriggerStyle()">
              <a href="/docs">Docs</a>
            </NavigationMenuLink>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuTrigger>List</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul class="grid w-[300px] gap-4">
                <li>
                  <NavigationMenuLink as-child>
                    <a href="#">
                      <div class="font-medium">Components</div>
                      <div class="text-muted-foreground">
                        Browse all components in the library.
                      </div>
                    </a>
                  </NavigationMenuLink>
                  <NavigationMenuLink as-child>
                    <a href="#">
                      <div class="font-medium">Documentation</div>
                      <div class="text-muted-foreground">
                        Learn how to use the library.
                      </div>
                    </a>
                  </NavigationMenuLink>
                  <NavigationMenuLink as-child>
                    <a href="#">
                      <div class="font-medium">Blog</div>
                      <div class="text-muted-foreground">
                        Read our latest blog posts.
                      </div>
                    </a>
                  </NavigationMenuLink>
                </li>
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuTrigger>Simple</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul class="grid w-[200px] gap-4">
                <li>
                  <NavigationMenuLink as-child>
                    <a href="#">Components</a>
                  </NavigationMenuLink>
                  <NavigationMenuLink as-child>
                    <a href="#">Documentation</a>
                  </NavigationMenuLink>
                  <NavigationMenuLink as-child>
                    <a href="#">Blocks</a>
                  </NavigationMenuLink>
                </li>
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuTrigger>With Icon</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul class="grid w-[200px] gap-4">
                <li>
                  <NavigationMenuLink as-child>
                    <a href="#" class="flex-row items-center gap-2">
                      <CircleHelpIcon />
                      Backlog
                    </a>
                  </NavigationMenuLink>
                  <NavigationMenuLink as-child>
                    <a href="#" class="flex-row items-center gap-2">
                      <CircleIcon />
                      To Do
                    </a>
                  </NavigationMenuLink>
                  <NavigationMenuLink as-child>
                    <a href="#" class="flex-row items-center gap-2">
                      <CircleCheckIcon />
                      Done
                    </a>
                  </NavigationMenuLink>
                </li>
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
        </NavigationMenuList>
      </NavigationMenu>
    </div>

    <!-- Main Content -->
    <div class="flex justify-center px-8 py-16">
      <Card class="w-full max-w-4xl">
        <CardHeader class="gap-4">
          <CardTitle>Stroke Analysis Course</CardTitle>
          <CardDescription class="mt-4">
            Welcome to the Stroke Analysis course. Please choose which Cohort you are enrolled in to get started.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div class="flex flex-row gap-8 justify-center py-4">
            <Button variant="outline" class="w-64 h-24" @click="onClick(1)">
              Cohort 1 - Teacher Led
            </Button>
            <Button variant="outline" class="w-64 h-24" @click="onClick(2)">
              Cohort 2 - Teacher + AI Led
            </Button>
            <Button variant="outline" class="w-64 h-24" @click="onClick(3)">
              Cohort 3 - AI Led
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<style scoped>
</style>  