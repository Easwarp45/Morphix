/* =============================================================================
   Landing Page â€” Hero, Features, How It Works, CTA
   ============================================================================= */

import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  FileText, Image, Archive, Zap, Shield,
  ArrowRight, Sparkles, CheckCircle2, Globe,
} from 'lucide-react';

const features = [
  { icon: FileText, title: 'Document Conversion', desc: 'PDF â†” DOCX, TXT â†” PDF with layout preservation', color: 'from-blue-500 to-cyan-500' },
  { icon: Image, title: 'Image Conversion', desc: 'PNG, JPG, WEBP â€” convert and compress instantly', color: 'from-purple-500 to-pink-500' },
  { icon: Archive, title: 'Archive Support', desc: 'Create and extract ZIP archives securely', color: 'from-amber-500 to-orange-500' },
  { icon: Shield, title: 'Secure Processing', desc: 'End-to-end encryption, files auto-deleted', color: 'from-emerald-500 to-teal-500' },
  { icon: Zap, title: 'Lightning Fast', desc: 'Async processing with real-time progress', color: 'from-rose-500 to-red-500' },
  { icon: Globe, title: 'Cloud Native', desc: 'Access from anywhere, no software install', color: 'from-indigo-500 to-violet-500' },
];

const steps = [
  { num: '01', title: 'Upload', desc: 'Drag & drop your files or click to browse' },
  { num: '02', title: 'Choose Format', desc: 'Select your target format from supported types' },
  { num: '03', title: 'Convert & Download', desc: 'Get your converted file in seconds' },
];

const stats = [
  { value: '20+', label: 'Formats Supported' },
  { value: '100MB', label: 'Max File Size' },
  { value: 'Instant', label: 'Guest Mode' },
  { value: '100%', label: 'Free Utility' },
];

export function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      {/* â”€â”€ Hero Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="relative min-h-screen flex items-center justify-center gradient-bg pt-16">
        {/* Gradient orbs */}
        <div className="gradient-orb w-96 h-96 bg-primary-500/30 -top-20 -left-20" />
        <div className="gradient-orb w-72 h-72 bg-purple-500/20 top-40 right-10" style={{ animationDelay: '2s' }} />
        <div className="gradient-orb w-80 h-80 bg-pink-500/15 bottom-20 left-1/3" style={{ animationDelay: '4s' }} />

        <div className="relative z-10 max-w-5xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            {/* Badge */}
            <div className="inline-flex items-center px-4 py-1.5 rounded-full glass text-sm mb-8">
              <Sparkles className="w-4 h-4 text-primary-400 mr-2" />
              <span className="text-gray-300">Powered by cloud-native architecture</span>
            </div>

            {/* Heading */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-tight mb-6">
              Convert Files
              <br />
              <span className="gradient-text">In The Cloud</span>
            </h1>

            <p className="text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              Transform documents, images, and archives between formats instantly.
              Professional-grade conversion engine with drag-and-drop simplicity.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/convert"
                className="group px-8 py-4 rounded-2xl text-lg font-semibold bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-all shadow-2xl shadow-primary-500/30 hover:shadow-primary-500/50 flex items-center"
                id="hero-cta"
              >
                Convert Files Now
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/register"
                className="px-8 py-4 rounded-2xl text-lg font-semibold glass text-white hover:bg-white/10 transition-colors"
              >
                Sign Up (100MB Limit)
              </Link>
            </div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-20 grid grid-cols-2 sm:grid-cols-4 gap-6"
          >
            {stats.map((stat) => (
              <div key={stat.label} className="glass rounded-2xl p-5 text-center">
                <div className="text-3xl font-black text-white mb-1">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* â”€â”€ Features Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-24 relative" id="features">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">
              Everything You Need to{' '}
              <span className="gradient-text">Convert Files</span>
            </h2>
            <p className="text-lg text-[hsl(var(--muted-foreground))] max-w-2xl mx-auto">
              Professional conversion tools that handle documents, images, compression, and archives with precision.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="group p-6 rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] hover:border-primary-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-primary-500/5"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-[hsl(var(--muted-foreground))] text-sm leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ How It Works â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-24 bg-[hsl(var(--card))]">
        <div className="max-w-5xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">
              How It <span className="gradient-text">Works</span>
            </h2>
            <p className="text-lg text-[hsl(var(--muted-foreground))]">Three simple steps to convert any file</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="text-center"
              >
                <div className="text-6xl font-black gradient-text mb-4">{step.num}</div>
                <h3 className="text-xl font-semibold mb-2">{step.title}</h3>
                <p className="text-[hsl(var(--muted-foreground))]">{step.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ CTA Section â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-24 relative">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="p-12 rounded-3xl bg-gradient-to-br from-primary-600/20 via-purple-600/20 to-pink-600/20 border border-primary-500/20"
          >
            <h2 className="text-4xl font-bold mb-4">
              Ready to Start Converting?
            </h2>
            <p className="text-lg text-[hsl(var(--muted-foreground))] mb-8 max-w-lg mx-auto">
              Join thousands of users who trust morphixert for their file conversion needs.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center px-8 py-4 rounded-2xl text-lg font-semibold bg-gradient-to-r from-primary-500 to-purple-600 text-white hover:opacity-90 transition-all shadow-2xl shadow-primary-500/30"
              id="bottom-cta"
            >
              Get Started â€” It&apos;s Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>

            <div className="flex items-center justify-center gap-6 mt-8 text-sm text-[hsl(var(--muted-foreground))]">
              <span className="flex items-center"><CheckCircle2 className="w-4 h-4 mr-1.5 text-accent-500" /> Guest Mode (No Signup)</span>
              <span className="flex items-center"><CheckCircle2 className="w-4 h-4 mr-1.5 text-accent-500" /> OCR & AI Summary</span>
              <span className="flex items-center"><CheckCircle2 className="w-4 h-4 mr-1.5 text-accent-500" /> 100% Free Utility</span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* â”€â”€ Footer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <footer className="py-12 border-t border-[hsl(var(--border))]">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold">morphixert</span>
            </div>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">
              Â© {new Date().getFullYear()} Morphix. Built with â¤ï¸
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
