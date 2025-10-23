'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/BasicAuthContext'
import { useRouter } from 'next/navigation'
import LoginModal from '@/components/auth/LoginModal'
import { 
  Menu, 
  X,
  Play,
  MessageCircle,
  ArrowRight,
  CheckCircle,
  Database,
  Users,
  Lock,
  Star,
  ChevronRight,
  ExternalLink,
  Terminal,
  FileText,
  Brain,
  Rocket,
  Download,
  Upload,
  Eye,
  Search,
  Zap,
  BookOpen
} from 'lucide-react'

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [showLoginModal, setShowLoginModal] = useState(false)
  const [hasRedirected, setHasRedirected] = useState(false)
  const { user, loading } = useAuth()
  const router = useRouter()

  // Redirect to dashboard if user is already authenticated (only once)
  useEffect(() => {
    if (!loading && user && !hasRedirected) {
      // Add a small delay to prevent race conditions
      const redirectTimer = setTimeout(() => {
        setHasRedirected(true)
        router.push('/dashboard')
      }, 100)
      
      return () => clearTimeout(redirectTimer)
    }
  }, [user, loading, hasRedirected])

  const handleGetStarted = () => {
    setShowLoginModal(true)
  }

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3 mx-auto mb-4">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <p className="text-white/80">Loading...</p>
        </div>
      </div>
    )
  }

  // Prevent rendering if redirecting
  if (hasRedirected) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3 mx-auto mb-4">
            <FileText className="w-4 h-4 text-white" />
          </div>
          <p className="text-white/80">Redirecting to dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black text-white overflow-x-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-black/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                <FileText className="w-4 h-4 text-white" />
              </div>
              <span className="text-xl font-semibold text-white">LabMate</span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-white hover:text-white/80 transition-colors">Features</a>
              <a href="#how-it-works" className="text-white hover:text-white/80 transition-colors">How it Works</a>
              <a href="#pricing" className="text-white hover:text-white/80 transition-colors">Pricing</a>
              <a href="#docs" className="text-white hover:text-white/80 transition-colors">Docs</a>
              <a href="#contact" className="text-white hover:text-white/80 transition-colors">Contact</a>
            </div>

            {/* Right side buttons */}
            <div className="hidden md:flex items-center space-x-4">
              <MessageCircle className="w-5 h-5 text-white hover:text-white/80 cursor-pointer" />
              <button className="text-white hover:text-white/80 transition-colors px-4 py-2 rounded-lg">
                Sign In
              </button>
              <button 
                onClick={handleGetStarted}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center gap-2"
              >
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE3LjY0IDkuMjA0NTVDMTcuNjQgOC41NjYzNiAxNy41ODI3IDcuOTUyNzMgMTcuNDc2NCA3LjM2MzY0SDkuMTgwNDVWMTEuMDEzNkgxNC4wNDA5QzEzLjc4MjcgMTIuMjk1NSAxMy4wNjgyIDEzLjM3MjcgMTIuMDA5MSAxNC4wNjM2VjE2LjU3NzNIOC4xODQ1NUMxMC4xMjcyIDE0Ljg0NTUgMTEuMTgxOCAxMi4zNDA5IDExLjE4MTggOS4yMDQ1NVoiIGZpbGw9IiM0Mjg1RjQiLz4KPHBhdGggZD0iTTkuMTgwNDUgMTguMDAwMUMxMS40MzY0IDE4LjAwMDEgMTMuMjY4MiAxNy4yNzI3IDE0LjUxMzYgMTYuMDYzNkwxMi4wMDkxIDE0LjA2MzZDMTEuMzE4MiAxNC41NjM2IDEwLjMyMjcgMTQuOTA5MSA5LjE4MDQ1IDE0LjkwOTFDNi45NzI3MyAxNC45MDkxIDUuMTE4MTggMTMuMzY4MiA0LjQ0NzI3IDExLjQ5NTVIOC4xODQ1NVYxNi41NzczSDkuMTgwNDVaIiBmaWxsPSIjMzRBODUzIi8+CjxwYXRoIGQ9Ik00LjQ0NzI3IDkuMjA0NTVDNC4yNjM2NCA4LjQzMTgyIDQuMjYzNjQgNy41NjgxOCA0LjQ0NzI3IDYuNzk1NDVWMy43MTM2NEg5LjE4MDQ1VjkuMjA0NDVINC40NDcyN1oiIGZpbGw9IiNGQkJDMzMiLz4KPHBhdGggZD0iTTkuMTgwNDUgMTcuNTU0NUg0LjQ0NzI3VjE0LjQ3MjhDNS4xMTgxOCAxNS4zNDA5IDYuOTcyNzMgMTYuODgxOCA5LjE4MDQ1IDE2Ljg4MThaIiBmaWxsPSIjRUE0MzM1Ii8+CjxwYXRoIGQ9Ik0xNy42NCA5LjIwNDU1QzE3LjY0IDguNTY2MzYgMTcuNTgyNyA3Ljk1MjczIDE3LjQ3NjQgNy4zNjM2NEg5LjE4MDQ1VjExLjAxMzZIMTQuMDQwOUMxMy43ODI3IDEyLjI5NTUgMTMuMDY4MiAxMy4zNzI3IDEyLjAwOTEgMTQuMDYzNlYxNi41NzczSDguMTg0NTVDMTAuMTI3MiAxNC44NDU1IDExLjE4MTggMTIuMzQwOSAxMS4xODE4IDkuMjA0NTVaIiBmaWxsPSIjNDI4NUY0Ii8+Cjwvc3ZnPgo=" alt="Google" className="w-4 h-4" />
                Get Started
              </button>
            </div>

            {/* Mobile menu button */}
            <button 
              className="md:hidden text-white"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-black/95 backdrop-blur-md border-t border-white/10">
            <div className="px-4 py-4 space-y-4">
              <a href="#features" className="block text-white hover:text-white/80 transition-colors">Features</a>
              <a href="#how-it-works" className="block text-white hover:text-white/80 transition-colors">How it Works</a>
              <a href="#pricing" className="block text-white hover:text-white/80 transition-colors">Pricing</a>
              <a href="#docs" className="block text-white hover:text-white/80 transition-colors">Docs</a>
              <a href="#contact" className="block text-white hover:text-white/80 transition-colors">Contact</a>
              <div className="flex items-center space-x-4 pt-4">
                <MessageCircle className="w-5 h-5 text-white" />
                <button className="text-white px-4 py-2 rounded-lg">Sign In</button>
                <button 
                  onClick={handleGetStarted}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2"
                >
                  <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE3LjY0IDkuMjA0NTVDMTcuNjQgOC41NjYzNiAxNy41ODI3IDcuOTUyNzMgMTcuNDc2NCA3LjM2MzY0SDkuMTgwNDVWMTEuMDEzNkgxNC4wNDA5QzEzLjc4MjcgMTIuMjk1NSAxMy4wNjgyIDEzLjM3MjcgMTIuMDA5MSAxNC4wNjM2VjE2LjU3NzNIOC4xODQ1NUMxMC4xMjcyIDE0Ljg0NTUgMTEuMTgxOCAxMi4zNDA5IDExLjE4MTggOS4yMDQ1NVoiIGZpbGw9IiM0Mjg1RjQiLz4KPHBhdGggZD0iTTkuMTgwNDUgMTguMDAwMUMxMS40MzY0IDE4LjAwMDEgMTMuMjY4MiAxNy4yNzI3IDE0LjUxMzYgMTYuMDYzNkwxMi4wMDkxIDE0LjA2MzZDMTEuMzE4MiAxNC41NjM2IDEwLjMyMjcgMTQuOTA5MSA5LjE4MDQ1IDE0LjkwOTFDNi45NzI3MyAxNC45MDkxIDUuMTE4MTggMTMuMzY4MiA0LjQ0NzI3IDExLjQ5NTVIOC4xODQ1NVYxNi41NzczSDkuMTgwNDVaIiBmaWxsPSIjMzRBODUzIi8+CjxwYXRoIGQ9Ik00LjQ0NzI3IDkuMjA0NTVDNC4yNjM2NCA4LjQzMTgyIDQuMjYzNjQgNy41NjgxOCA0LjQ0NzI3IDYuNzk1NDVWMy43MTM2NEg5LjE4MDQ1VjkuMjA0NDVINC40NDcyN1oiIGZpbGw9IiNGQkJDMzMiLz4KPHBhdGggZD0iTTkuMTgwNDUgMTcuNTU0NUg0LjQ0NzI3VjE0LjQ3MjhDNS4xMTgxOCAxNS4zNDA5IDYuOTcyNzMgMTYuODgxOCA5LjE4MDQ1IDE2Ljg4MThaIiBmaWxsPSIjRUE0MzM1Ii8+CjxwYXRoIGQ9Ik0xNy42NCA5LjIwNDU1QzE3LjY0IDguNTY2MzYgMTcuNTgyNyA3Ljk1MjczIDE3LjQ3NjQgNy4zNjM2NEg5LjE4MDQ1VjExLjAxMzZIMTQuMDQwOUMxMy43ODI3IDEyLjI5NTUgMTMuMDY4MiAxMy4zNzI3IDEyLjAwOTEgMTQuMDYzNlYxNi41NzczSDguMTg0NTVDMTAuMTI3MiAxNC44NDU1IDExLjE4MTggMTIuMzQwOSAxMS4xODE4IDkuMjA0NTVaIiBmaWxsPSIjNDI4NUY0Ii8+Cjwvc3ZnPgo=" alt="Google" className="w-4 h-4" />
                  Get Started
                </button>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 relative overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0">
          <div className="absolute bottom-0 left-0 w-full h-96 bg-gradient-to-r from-blue-500/20 via-cyan-400/30 to-transparent rounded-full blur-3xl transform translate-x-[-20%]"></div>
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-5xl md:text-7xl font-bold mb-6"
          >
            What will you{' '}
            <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              build
            </span>{' '}
            today?
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-xl text-white/80 mb-12 max-w-2xl mx-auto"
          >
            Create stunning lab assignments with AI-powered code analysis, automated execution, and professional reports.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-8"
          >
            <div className="flex-1 max-w-2xl">
              <input
                type="text"
                placeholder="Upload your lab assignment and let AI analyze it..."
                className="w-full px-6 py-4 bg-gray-900 border border-white/20 rounded-xl text-white placeholder-white/60 focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl flex items-center justify-center gap-2 transition-colors">
              <Play className="w-5 h-5" />
              Analyze Now
            </button>
          </motion.div>

        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-6xl font-bold mb-6">
              <span className="text-white">
                Everything you need to
              </span>
              <br />
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                excel in coding
              </span>
            </h2>
            <p className="text-xl text-white/80 max-w-3xl mx-auto">
              From intelligent code analysis to automated testing and professional documentation, 
              LabMate provides all the tools you need for successful assignments.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: Search,
                title: "AI Code Analysis",
                description: "Intelligent analysis of your code with suggestions for improvements and best practices.",
                color: "from-blue-500 to-cyan-500"
              },
              {
                icon: Zap,
                title: "Automated Execution",
                description: "Run your code in a secure sandbox environment with real-time output and error handling.",
                color: "from-green-500 to-emerald-500"
              },
              {
                icon: BookOpen,
                title: "Smart Documentation",
                description: "Generate professional reports with embedded screenshots and detailed explanations.",
                color: "from-purple-500 to-pink-500"
              },
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group p-8 rounded-3xl bg-gray-900/50 border border-white/10 hover:border-white/20 hover:bg-gray-900/70 transition-all duration-300 text-center"
                whileHover={{ scale: 1.02, y: -5 }}
              >
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.color} p-4 mb-6 group-hover:scale-110 transition-transform duration-300 mx-auto`}>
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold mb-4 group-hover:text-white transition-colors text-center">
                  {feature.title}
                </h3>
                <p className="text-white/80 group-hover:text-white/90 transition-colors text-center">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section 
        id="how-it-works" 
        className="py-20 px-4 sm:px-6 lg:px-8 relative"
        style={{
          backgroundImage: 'url(/wavy_background.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      >
        {/* Dark overlay for better text readability */}
        <div className="absolute inset-0 bg-black/60"></div>
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-6xl font-bold mb-6">
              How LabMate Works
            </h2>
            <p className="text-xl text-white/80 max-w-3xl mx-auto">
              Get your assignments done in 4 simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                step: "01",
                title: "Upload",
                description: "Upload your DOCX or PDF lab assignment document"
              },
              {
                step: "02", 
                title: "AI Analysis",
                description: "Our AI analyzes and extracts code blocks and requirements"
              },
              {
                step: "03",
                title: "Execute",
                description: "Code runs automatically in secure sandbox environment"
              },
              {
                step: "04",
                title: "Report",
                description: "Get professional report with screenshots and explanations"
              }
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-white font-bold text-lg">{step.step}</span>
                </div>
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-white/80">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-4 sm:px-6 lg:px-8 relative">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="relative"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-purple-600/20 rounded-3xl blur-3xl"></div>
            <div className="relative p-12 rounded-3xl bg-gray-900/50 border border-white/10">
              <h2 className="text-4xl md:text-6xl font-bold mb-6">
                <span className="text-white">
                  Ready to transform
                </span>
                <br />
                <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  your assignments?
                </span>
              </h2>
              <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
                Join thousands of students who are already building better assignments with LabMate AI.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button 
                  onClick={handleGetStarted}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAxOCAxOCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE3LjY0IDkuMjA0NTVDMTcuNjQgOC41NjYzNiAxNy41ODI3IDcuOTUyNzMgMTcuNDc2NCA3LjM2MzY0SDkuMTgwNDVWMTEuMDEzNkgxNC4wNDA5QzEzLjc4MjcgMTIuMjk1NSAxMy4wNjgyIDEzLjM3MjcgMTIuMDA5MSAxNC4wNjM2VjE2LjU3NzNIOC4xODQ1NUMxMC4xMjcyIDE0Ljg0NTUgMTEuMTgxOCAxMi4zNDA5IDExLjE4MTggOS4yMDQ1NVoiIGZpbGw9IiM0Mjg1RjQiLz4KPHBhdGggZD0iTTkuMTgwNDUgMTguMDAwMUMxMS40MzY0IDE4LjAwMDEgMTMuMjY4MiAxNy4yNzI3IDE0LjUxMzYgMTYuMDYzNkwxMi4wMDkxIDE0LjA2MzZDMTEuMzE4MiAxNC41NjM2IDEwLjMyMjcgMTQuOTA5MSA5LjE4MDQ1IDE0LjkwOTFDNi45NzI3MyAxNC45MDkxIDUuMTE4MTggMTMuMzY4MiA0LjQ0NzI3IDExLjQ5NTVIOC4xODQ1NVYxNi41NzczSDkuMTgwNDVaIiBmaWxsPSIjMzRBODUzIi8+CjxwYXRoIGQ9Ik00LjQ0NzI3IDkuMjA0NTVDNC4yNjM2NCA4LjQzMTgyIDQuMjYzNjQgNy41NjgxOCA0LjQ0NzI3IDYuNzk1NDVWMy43MTM2NEg5LjE4MDQ1VjkuMjA0NDVINC40NDcyN1oiIGZpbGw9IiNGQkJDMzMiLz4KPHBhdGggZD0iTTkuMTgwNDUgMTcuNTU0NUg0LjQ0NzI3VjE0LjQ3MjhDNS4xMTgxOCAxNS4zNDA5IDYuOTcyNzMgMTYuODgxOCA5LjE4MDQ1IDE2Ljg4MThaIiBmaWxsPSIjRUE0MzM1Ii8+CjxwYXRoIGQ9Ik0xNy42NCA5LjIwNDU1QzE3LjY0IDguNTY2MzYgMTcuNTgyNyA3Ljk1MjczIDE3LjQ3NjQgNy4zNjM2NEg5LjE4MDQ1VjExLjAxMzZIMTQuMDQwOUMxMy43ODI3IDEyLjI5NTUgMTMuMDY4MiAxMy4zNzI3IDEyLjAwOTEgMTQuMDYzNlYxNi41NzczSDguMTg0NTVDMTAuMTI3MiAxNC44NDU1IDExLjE4MTggMTIuMzQwOSAxMS4xODE4IDkuMjA0NTVaIiBmaWxsPSIjNDI4NUY0Ii8+Cjwvc3ZnPgo=" alt="Google" className="w-4 h-4" />
                  Start Free Trial
                </button>
                <button className="bg-white/10 hover:bg-white/20 text-white px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-300">
                  View Pricing
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-16 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-5 gap-8 mb-12">
            <div>
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mr-3 relative">
                  {/* Northeast Arrow */}
                  <div className="absolute top-1 right-1 w-0 h-0 border-l-[4px] border-l-transparent border-b-[6px] border-b-white transform rotate-45"></div>
                  {/* Southwest Arrow */}
                  <div className="absolute bottom-1 left-1 w-0 h-0 border-r-[4px] border-r-transparent border-t-[6px] border-t-white transform rotate-45"></div>
                </div>
                <span className="text-xl font-semibold">LabMate</span>
              </div>
              <p className="text-white/60 mb-4">
                AI-powered platform for coding assignments and lab reports.
              </p>
              <div className="flex space-x-4">
                <MessageCircle className="w-5 h-5 text-white/60 hover:text-white cursor-pointer" />
              </div>
            </div>
            
            {[
              {
                title: "Product",
                links: ["Features", "How it Works", "Pricing", "API"]
              },
              {
                title: "Company", 
                links: ["About", "Blog", "Careers", "Contact"]
              },
              {
                title: "Resources",
                links: ["Docs", "Support", "Community", "Security"]
              },
              {
                title: "Legal",
                links: ["Privacy Policy", "Terms of Service", "Cookie Policy"]
              }
            ].map((section, index) => (
              <div key={index}>
                <h3 className="font-semibold mb-4 text-white">{section.title}</h3>
                <ul className="space-y-2">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <a href="#" className="text-white/60 hover:text-white transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          
          <div className="border-t border-white/10 pt-8">
            <p className="text-white/60 text-sm">
              © 2024 LabMate. All rights reserved.
            </p>
          </div>
        </div>
      </footer>


      {/* Login Modal */}
      <LoginModal isOpen={showLoginModal} onClose={() => setShowLoginModal(false)} />
    </div>
  )
}