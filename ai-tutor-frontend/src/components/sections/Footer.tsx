"use client"

import { Heart } from "lucide-react"

const footerLinks = {
  Product: ["Features", "Pricing", "API", "Changelog"],
  Company: ["About", "Blog", "Careers", "Contact"],
  Support: ["Docs", "Tutorials", "Status", "FAQ"],
  Legal: ["Privacy", "Terms", "Security", "Cookies"],
}

export default function Footer() {
  return (
    <footer className="border-t border-border/30 section-padding pb-8">
      <div className="max-width">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h4 className="text-xs uppercase tracking-[0.15em] text-muted-foreground font-medium mb-4">
                {title}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-sm text-muted-foreground/80 hover:text-foreground transition-colors"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-border/20 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-[8px] leading-tight text-center">SMIT</span>
            </div>
            <span className="text-sm font-medium leading-tight">ASSISTANT<br />TUTOR</span>
          </div>

          <p className="text-xs text-muted-foreground flex items-center gap-1">
            Built with <Heart className="w-3 h-3 text-red-500 fill-red-500" /> for better teaching
          </p>

          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} SMIT ASSISTANT TUTOR. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
