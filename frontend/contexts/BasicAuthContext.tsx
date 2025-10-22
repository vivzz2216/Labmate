'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { apiService } from '../lib/api'

interface User {
  id: number
  email: string
  name: string
  profile_picture?: string
  created_at: string
  last_login: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  signup: (email: string, name: string, password: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  getCurrentUser: () => User | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check if user is stored in localStorage
    const checkStoredUser = () => {
      try {
        const storedUser = localStorage.getItem('labmate_user')
        if (storedUser) {
          const userData = JSON.parse(storedUser)
          setUser(userData)
        }
      } catch (error) {
        console.error('Error loading stored user:', error)
        localStorage.removeItem('labmate_user')
      } finally {
        setLoading(false)
      }
    }

    checkStoredUser()
  }, [])

  const signup = async (email: string, name: string, password: string) => {
    try {
      setLoading(true)
      const userData = await apiService.signup(email, name, password)
      
      // Store user in localStorage
      localStorage.setItem('labmate_user', JSON.stringify(userData))
      setUser(userData)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (error) {
      console.error('Signup failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      setLoading(true)
      const userData = await apiService.login(email, password)
      
      // Store user in localStorage
      localStorage.setItem('labmate_user', JSON.stringify(userData))
      setUser(userData)
      
      // Redirect to dashboard
      router.push('/dashboard')
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    try {
      setLoading(true)
      
      // Remove user from localStorage
      localStorage.removeItem('labmate_user')
      setUser(null)
      
      // Redirect to homepage
      router.push('/')
    } catch (error) {
      console.error('Signout failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCurrentUser = () => {
    return user
  }

  const value = {
    user,
    loading,
    signup,
    login,
    signOut,
    getCurrentUser
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
