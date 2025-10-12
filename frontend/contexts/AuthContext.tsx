'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { 
  User as FirebaseUser,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut as firebaseSignOut,
  onAuthStateChanged
} from 'firebase/auth'
import { auth, googleProvider } from '@/lib/firebase'
import { useRouter } from 'next/navigation'

interface User {
  id: number
  google_id: string
  email: string
  name: string
  profile_picture?: string
  created_at: string
  last_login: string
}

interface AuthContextType {
  user: User | null
  firebaseUser: FirebaseUser | null
  loading: boolean
  signInWithGoogle: () => Promise<void>
  signInWithGoogleRedirect: () => Promise<void>
  signOut: () => Promise<void>
  getCurrentUser: () => User | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    if (!auth) {
      setLoading(false);
      return;
    }
    
    // Check for redirect result first
    const checkRedirectResult = async () => {
      try {
        const result = await getRedirectResult(auth)
        if (result) {
          console.log('Redirect authentication successful:', result.user.email)
        }
      } catch (error) {
        console.error('Redirect result error:', error)
      }
    }
    
    checkRedirectResult()
    
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setFirebaseUser(firebaseUser)
      
      if (firebaseUser) {
        // Get ID token and send to backend
        const idToken = await firebaseUser.getIdToken()
        try {
          const response = await fetch('http://localhost:8000/api/auth/google', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id_token: idToken }),
          })
          
          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
          } else {
            console.error('Failed to authenticate with backend')
            setUser(null)
          }
        } catch (error) {
          console.error('Error authenticating with backend:', error)
          setUser(null)
        }
      } else {
        setUser(null)
      }
      
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const signInWithGoogleRedirect = async () => {
    try {
      setLoading(true)
      if (!auth || !googleProvider) {
        throw new Error('Firebase authentication not available')
      }
      
      // Use redirect instead of popup to avoid CORS issues
      await signInWithRedirect(auth, googleProvider)
      // The page will redirect, so we don't need to handle the result here
    } catch (error) {
      console.error('Error with redirect sign-in:', error)
      setLoading(false)
      alert('Authentication redirect failed. Please try again.')
    }
  }

  const signInWithGoogle = async () => {
    try {
      setLoading(true)
      if (!auth || !googleProvider) {
        // Simulate successful authentication in development mode
        console.log('Firebase not available, using development mode')
        const mockUser = {
          id: 1,
          google_id: 'dev_user_123',
          email: 'dev@example.com',
          name: 'Development User',
          profile_picture: undefined,
          created_at: new Date().toISOString(),
          last_login: new Date().toISOString()
        }
        setUser(mockUser)
        setLoading(false)
        router.push('/user-dashboard')
        return
      }
      
      // Configure popup settings to reduce CORS issues
      googleProvider.setCustomParameters({
        prompt: 'select_account'
      })
      
      try {
        const result = await signInWithPopup(auth, googleProvider)
        // The onAuthStateChanged will handle the rest
        console.log('Google sign-in successful:', result.user.email)
      } catch (popupError: any) {
        console.warn('Popup authentication failed:', popupError)
        
        // If popup fails due to CORS, show a helpful message
        if (popupError.code === 'auth/popup-blocked' || 
            popupError.message?.includes('Cross-Origin-Opener-Policy') ||
            popupError.message?.includes('popup')) {
          
          // Show user-friendly instructions with multiple options
          const choice = confirm(
            'Your browser is blocking the authentication popup.\n\n' +
            'Click OK to use redirect authentication (recommended), or Cancel to continue without authentication.'
          )
          
          if (choice) {
            // Use redirect authentication instead
            console.log('Using redirect authentication due to popup blocking')
            return signInWithGoogleRedirect()
          } else {
            // Use development mode as fallback
            console.log('Using development mode due to popup blocking')
            const mockUser = {
              id: 1,
              google_id: 'dev_user_123',
              email: 'dev@example.com',
              name: 'Development User',
              profile_picture: undefined,
              created_at: new Date().toISOString(),
              last_login: new Date().toISOString()
            }
            setUser(mockUser)
            setLoading(false)
            router.push('/user-dashboard')
            return
          }
        }
        
        throw popupError
      }
    } catch (error: any) {
      console.error('Error signing in with Google:', error)
      setLoading(false)
      
      // Show specific error message based on error type
      let errorMessage = 'Authentication failed. Please try again.'
      if (error.code === 'auth/popup-closed-by-user') {
        errorMessage = 'Sign-in was cancelled. Please try again if you want to continue.'
      } else if (error.code === 'auth/popup-blocked') {
        errorMessage = 'Popup was blocked by your browser. Please allow popups for this site.'
      } else if (error.message?.includes('Cross-Origin-Opener-Policy')) {
        errorMessage = 'Browser security policy is blocking authentication. Please check your browser settings.'
      }
      
      alert(errorMessage)
    }
  }

  const signOut = async () => {
    try {
      setLoading(true)
      if (auth) {
        await firebaseSignOut(auth)
      }
      setUser(null)
      setFirebaseUser(null)
      router.push('/')
    } catch (error) {
      console.error('Error signing out:', error)
      setLoading(false)
    }
  }

  const getCurrentUser = () => {
    return user
  }

  const value = {
    user,
    firebaseUser,
    loading,
    signInWithGoogle,
    signInWithGoogleRedirect,
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
