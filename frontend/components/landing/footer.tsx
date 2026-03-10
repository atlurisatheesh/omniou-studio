import Link from "next/link";
import { Sparkles, Github, Twitter } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-border py-12 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div>
            <Link href="/" className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-primary" />
              <span className="font-bold">
                Clone<span className="text-primary">AI</span> Pro
              </span>
            </Link>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Your face. Your voice. Any language. Free forever. Open source
              AI avatar video generator.
            </p>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Product
            </h4>
            <div className="space-y-2">
              <Link href="#features" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Features
              </Link>
              <Link href="#pricing" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Pricing
              </Link>
              <Link href="/dashboard/create" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Create Video
              </Link>
              <Link href="/docs" className="block text-sm text-muted-foreground hover:text-foreground transition">
                API Docs
              </Link>
            </div>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Resources
            </h4>
            <div className="space-y-2">
              <a href="https://github.com/cloneai-pro/cloneai-pro" target="_blank" rel="noopener" className="block text-sm text-muted-foreground hover:text-foreground transition">
                GitHub
              </a>
              <Link href="/docs" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Documentation
              </Link>
              <Link href="/blog" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Blog
              </Link>
              <Link href="/changelog" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Changelog
              </Link>
            </div>
          </div>

          {/* Legal */}
          <div>
            <h4 className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Legal
            </h4>
            <div className="space-y-2">
              <Link href="/privacy" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Privacy Policy
              </Link>
              <Link href="/terms" className="block text-sm text-muted-foreground hover:text-foreground transition">
                Terms of Service
              </Link>
              <Link href="/license" className="block text-sm text-muted-foreground hover:text-foreground transition">
                MIT License
              </Link>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8 border-t border-border">
          <p className="text-xs text-muted-foreground">
            {new Date().getFullYear()} CloneAI Pro. Open source under MIT license.
          </p>
          <div className="flex items-center gap-4">
            <a href="https://github.com/cloneai-pro" target="_blank" rel="noopener" title="GitHub" className="text-muted-foreground hover:text-foreground transition">
              <Github className="w-4 h-4" />
            </a>
            <a href="https://twitter.com/cloneai_pro" target="_blank" rel="noopener" title="Twitter" className="text-muted-foreground hover:text-foreground transition">
              <Twitter className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
