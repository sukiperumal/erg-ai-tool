<script setup lang="ts">
import { ref } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import router from '@/router'

const email = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

async function onSubmit() {
  isLoading.value = true
  errorMessage.value = ''
  
  try {
    if (!email.value || !password.value) {
      errorMessage.value = 'Email and password are required'
      return
    }

    if (email.value !== 'jane@edunova.com' || password.value !== 'password') {
      errorMessage.value = 'Incorrect credentials'
      return
    }

    console.log('Login attempt:', { email: email.value, password: password.value })
    router.push({ name: 'home' })
  } catch (error) {
    console.error('Login failed:', error)
    errorMessage.value = 'Something went wrong'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-950 px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8 py-4">
        <h1 class="text-3xl font-semibold tracking-tight text-foreground">
          Sign in to your account
        </h1>
      </div>
      
      <Card class="border-0 shadow-lg shadow-gray-200/50 dark:shadow-none">
        <form @submit.prevent="onSubmit">
          <CardContent class="pt-6 pb-4">
            <div class="flex flex-col gap-5">
              <div>
                <label for="email" class="block text-sm font-medium mb-2">Email</label>
                <Input
                  id="email"
                  v-model="email"
                  type="email"
                  placeholder="you@example.com"
                  class="h-11"
                  required
                />
              </div>
              <div>
                <div class="flex items-center justify-between mb-2">
                  <label for="password" class="text-sm font-medium">Password</label>
                  <a href="/forgot-password" class="text-xs text-muted-foreground hover:text-foreground transition-colors">
                    Forgot password?
                  </a>
                </div>
                <Input
                  id="password"
                  v-model="password"
                  type="password"
                  placeholder="••••••••"
                  class="h-11"
                  required
                />
              </div>
            </div>
          </CardContent>
          <CardFooter class="flex flex-col pt-2 pb-6 space-y-3">
            <Button type="submit" class="w-full h-11 font-medium" :disabled="isLoading">
              <span v-if="isLoading">Signing in...</span>
              <span v-else>Sign in</span>
            </Button>
            <p v-if="errorMessage" class="text-sm text-red-500 text-center">
              {{ errorMessage }}
            </p>
          </CardFooter>
        </form>
      </Card>
      
      <p class="mt-6 text-center text-sm text-muted-foreground">
        Don't have an account?
        <a href="/register" class="font-medium text-foreground hover:underline underline-offset-4">
          Create one
        </a>
      </p>
    </div>
  </div>
</template>