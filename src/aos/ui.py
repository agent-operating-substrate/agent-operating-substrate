"""Local substrate visualizer and AI Behavior Control Plane web dashboard."""

from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Optional
import re
from urllib.parse import parse_qs, urlparse
import yaml

from aos.autopsy import inscribe_candidate, synthesize_candidate_rule
from aos.blackboard import post_event, read_events
from aos.curator import curate_substrate
from aos.discovery import discover_rules
from aos.engine import RuleEngine
from aos.fleet import list_fleet_rules
from aos.harness import format_rules_for_prompt, inject_into_file, sync_harnesses
from aos.hook import install_git_hook
from aos.mesh import simulate_mesh_cycle
from aos.packs import CURATED_PACKS, install_pack, list_available_packs
from aos.validator import validate_rule_dict

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AOS: AI Behavior Control Plane</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #0f172a;
      --card-hover: #162238;
      --border: #1e293b;
      --border-focus: #38bdf8;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0284c7;
      --primary-glow: rgba(56, 189, 248, 0.15);
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.15);
      --warning: #f59e0b;
      --warning-glow: rgba(245, 158, 11, 0.15);
      --danger: #ef4444;
      --danger-glow: rgba(239, 68, 68, 0.15);
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px 32px 64px;
      max-width: 1280px;
      margin: 0 auto;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .logo-badge {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #fff;
      font-weight: 800;
      font-size: 16px;
      letter-spacing: 1px;
      padding: 8px 12px;
      border-radius: 8px;
      box-shadow: 0 0 16px var(--primary-glow);
    }
    h1 {
      font-size: 20px;
      font-weight: 700;
      color: #fff;
      letter-spacing: -0.3px;
    }
    .hero-subtitle {
      color: var(--text-muted);
      font-size: 13px;
      margin-top: 2px;
    }
    .header-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: var(--success-glow);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 600;
      color: var(--success);
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      background: var(--success);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--success);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }
    .stats-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 28px;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .stat-card .label {
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.6px;
    }
    .stat-card .value {
      font-size: 26px;
      font-weight: 700;
      color: #fff;
      margin: 4px 0 2px;
    }
    .stat-card .subtext {
      font-size: 12px;
      color: var(--text-muted);
    }
    .tabs-nav {
      display: flex;
      gap: 6px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
    }
    .tab-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 14px;
      font-weight: 600;
      padding: 10px 18px;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .tab-btn:hover { color: var(--text); }
    .tab-btn.active {
      color: var(--primary);
      border-bottom-color: var(--primary);
    }
    .tab-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 20px;
      height: 20px;
      padding: 0 6px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 9999px;
      background: #1e293b;
      color: var(--text-muted);
      border: 1px solid var(--border);
      font-family: var(--font-mono);
      transition: all 0.2s;
    }
    .tab-btn.active .tab-badge {
      background: var(--primary-glow);
      color: var(--primary);
      border-color: rgba(56, 189, 248, 0.35);
    }
    .kbd-shortcut {
      font-size: 10px;
      font-family: var(--font-mono);
      padding: 1px 5px;
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: #64748b;
      margin-left: 2px;
    }
    .tab-btn.active .kbd-shortcut {
      color: var(--primary);
      border-color: rgba(56, 189, 248, 0.2);
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .btn {
      background: var(--card-bg);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s;
    }
    .btn:hover {
      background: var(--card-hover);
      border-color: #334155;
      color: #fff;
    }
    .btn-primary {
      background: #0284c7;
      color: #fff;
      border-color: #38bdf8;
    }
    .btn-primary:hover {
      background: #0369a1;
      border-color: #7dd3fc;
    }
    .btn-sm {
      padding: 5px 10px;
      font-size: 12px;
    }
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      gap: 12px;
      flex-wrap: wrap;
    }
    .search-container {
      position: relative;
      display: inline-flex;
      align-items: center;
    }
    .search-input {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 36px 8px 14px;
      border-radius: 6px;
      font-size: 13px;
      width: 330px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .search-input:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }
    .search-kbd {
      position: absolute;
      right: 10px;
      font-size: 11px;
      font-family: var(--font-mono);
      padding: 2px 6px;
      border-radius: 4px;
      background: #1e293b;
      border: 1px solid #334155;
      color: var(--text-muted);
      pointer-events: none;
    }
    .filter-group {
      display: flex;
      gap: 6px;
      align-items: center;
    }
    .filter-chip {
      background: var(--card-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      padding: 5px 12px;
      border-radius: 9999px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .filter-chip:hover, .filter-chip.active {
      color: #fff;
      background: #1e293b;
      border-color: #475569;
    }
    .rule-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    .rule-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s ease;
      cursor: pointer;
    }
    .rule-card:hover {
      border-color: #38bdf8;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
    }
    .rule-card.expanded {
      border-color: rgba(56, 189, 248, 0.45);
      background: #10192e;
    }
    .rule-details {
      margin-top: 14px;
      padding-top: 14px;
      border-top: 1px solid var(--border);
    }
    .rule-details-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 16px;
    }
    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .detail-label {
      font-size: 10.5px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      font-weight: 700;
    }
    .detail-value {
      font-size: 12px;
      color: #f1f5f9;
      word-break: break-all;
    }
    .detail-value.mono {
      font-family: var(--font-mono);
      color: var(--primary);
    }
    .rule-card-footer {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      margin-top: 10px;
      font-size: 11px;
    }
    .expand-cue {
      font-size: 11px;
      color: var(--primary);
      font-weight: 500;
      opacity: 0.85;
      transition: opacity 0.15s;
    }
    .rule-card:hover .expand-cue {
      opacity: 1;
    }
    .rule-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
      gap: 10px;
    }
    .rule-title-group {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .rule-id {
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 700;
      color: #f8fafc;
    }
    .badge {
      font-size: 10px;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.5px;
      padding: 2px 7px;
      border-radius: 4px;
    }
    .badge-block { background: var(--danger-glow); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-warn { background: var(--warning-glow); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-active { background: var(--success-glow); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-candidate { background: rgba(147, 51, 234, 0.15); color: #c084fc; border: 1px solid rgba(147, 51, 234, 0.3); }
    .badge-archive { background: rgba(100, 116, 139, 0.2); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }
    .switch-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .switch {
      position: relative;
      display: inline-block;
      width: 36px;
      height: 20px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #334155;
      transition: .2s;
      border-radius: 20px;
    }
    .slider:before {
      position: absolute;
      content: "";
      height: 14px;
      width: 14px;
      left: 3px;
      bottom: 3px;
      background-color: #fff;
      transition: .2s;
      border-radius: 50%;
    }
    input:checked + .slider { background-color: #10b981; }
    input:checked + .slider:before { transform: translateX(16px); }
    .rule-statement {
      font-size: 13.5px;
      color: #e2e8f0;
      font-weight: 500;
      margin-bottom: 8px;
    }
    .rule-rationale {
      font-size: 12px;
      color: var(--text-muted);
      font-style: italic;
      margin-bottom: 14px;
    }
    .rule-meta {
      font-size: 12px;
      color: var(--text-muted);
      padding-top: 12px;
      border-top: 1px solid #1e293b;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .chip {
      background: #1e293b;
      color: #cbd5e1;
      padding: 2px 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .tools-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .tool-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .tool-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .tool-name {
      font-size: 15px;
      font-weight: 700;
      color: #fff;
    }
    .tool-path {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--primary);
      margin-bottom: 8px;
    }
    .tool-desc {
      font-size: 12.5px;
      color: var(--text-muted);
      margin-bottom: 16px;
    }
    .sync-banner {
      background: linear-gradient(135deg, rgba(2, 132, 199, 0.15), rgba(56, 189, 248, 0.05));
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 10px;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      gap: 16px;
    }
    .sync-banner-text h3 {
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 4px;
    }
    .sync-banner-text p {
      font-size: 13px;
      color: var(--text-muted);
    }
    .incident-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .incident-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px 20px;
    }
    .incident-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .inspector-box {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 24px;
      margin-bottom: 24px;
    }
    .inspector-form {
      display: flex;
      gap: 12px;
      margin-top: 14px;
    }
    .inspector-input {
      flex: 1;
      background: #090d16;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 6px;
      font-family: var(--font-mono);
      font-size: 13px;
      outline: none;
    }
    .inspector-input:focus { border-color: var(--border-focus); }
    .modal-backdrop {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      opacity: 0;
      transition: opacity 0.25s ease;
      overflow-y: auto;
      padding: 24px 16px;
    }
    .modal-backdrop.open {
      opacity: 1;
    }
    .modal {
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 28px;
      width: 100%;
      max-width: 580px;
      max-height: calc(100vh - 48px);
      overflow-y: auto;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05);
      transform: scale(0.96) translateY(8px);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .modal-backdrop.open .modal {
      transform: scale(1) translateY(0);
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 4px;
    }
    .modal-close-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 20px;
      line-height: 1;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 4px;
      transition: color 0.15s, background 0.15s;
    }
    .modal-close-btn:hover {
      color: #fff;
      background: rgba(255, 255, 255, 0.1);
    }
    .modal-title {
      font-size: 18px;
      font-weight: 700;
      color: #fff;
    }
    .modal-subtitle {
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 20px;
    }
    .form-error {
      background: var(--danger-glow);
      border: 1px solid rgba(239, 68, 68, 0.35);
      color: #f87171;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 12.5px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .form-group {
      margin-bottom: 16px;
    }
    .form-group label {
      display: block;
      font-size: 12px;
      font-weight: 600;
      color: #cbd5e1;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .form-input, .form-select, .form-textarea {
      width: 100%;
      background: #090d16;
      border: 1px solid var(--border);
      color: var(--text);
      padding: 9px 12px;
      border-radius: 6px;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .form-input:focus, .form-select:focus, .form-textarea:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
    }
    .form-input.input-error, .form-textarea.input-error {
      border-color: #ef4444;
      box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.25);
    }
    .form-textarea {
      resize: vertical;
      min-height: 70px;
      font-family: inherit;
    }
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
    }
    .toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      z-index: 2000;
      pointer-events: none;
      max-width: calc(100vw - 48px);
    }
    .toast {
      pointer-events: auto;
      min-width: 300px;
      max-width: 440px;
      background: #0f172a;
      border: 1px solid #1e293b;
      color: #fff;
      padding: 12px 18px;
      border-radius: 8px;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
      font-size: 13px;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 12px;
      transform: translateY(16px);
      opacity: 0;
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.25s ease;
    }
    .toast.toast-visible {
      transform: translateY(0);
      opacity: 1;
    }
    .toast-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      font-size: 12px;
      font-weight: 700;
      flex-shrink: 0;
    }
    .toast-msg {
      flex: 1;
      word-break: break-word;
      line-height: 1.4;
    }
    .toast-success {
      border-color: rgba(16, 185, 129, 0.4);
      background: #062319;
      color: #ecfdf5;
    }
    .toast-success .toast-icon {
      background: rgba(16, 185, 129, 0.2);
      color: #10b981;
    }
    .toast-error {
      border-color: rgba(239, 68, 68, 0.4);
      background: #270d10;
      color: #fef2f2;
    }
    .toast-error .toast-icon {
      background: rgba(239, 68, 68, 0.2);
      color: #ef4444;
    }
    .toast-info {
      border-color: rgba(56, 189, 248, 0.4);
      background: #091a2e;
      color: #f0f9ff;
    }
    .toast-info .toast-icon {
      background: rgba(56, 189, 248, 0.2);
      color: #38bdf8;
    }
    .template-chip {
      background: #1e293b;
      border: 1px solid #334155;
      color: #93c5fd;
      font-size: 11.5px;
      font-weight: 600;
      padding: 5px 11px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .template-chip:hover {
      background: #0284c7;
      color: #fff;
      border-color: #38bdf8;
    }
    .verdict-banner {
      border-radius: 8px;
      padding: 16px 20px;
      margin-top: 14px;
      transition: all 0.2s ease;
    }
    .verdict-allowed {
      background: rgba(16, 185, 129, 0.1);
      border: 1px solid rgba(16, 185, 129, 0.4);
      color: #ecfdf5;
    }
    .verdict-blocked {
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fef2f2;
    }
    .verdict-header {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .verdict-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      font-weight: 800;
      font-size: 15px;
      flex-shrink: 0;
    }
    .verdict-allowed .verdict-icon {
      background: rgba(16, 185, 129, 0.25);
      color: #10b981;
    }
    .verdict-blocked .verdict-icon {
      background: rgba(239, 68, 68, 0.25);
      color: #ef4444;
    }
    .verdict-title {
      font-size: 14.5px;
      font-weight: 700;
    }
    .verdict-allowed .verdict-title { color: #34d399; }
    .verdict-blocked .verdict-title { color: #f87171; }
    .verdict-subtitle {
      font-size: 12.5px;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .violation-item {
      background: #090d16;
      border: 1px solid rgba(239, 68, 68, 0.3);
      border-radius: 6px;
      padding: 12px 14px;
    }
    .violation-snippet {
      background: #111827;
      border: 1px solid #1f2937;
      border-left: 3px solid #ef4444;
      padding: 8px 12px;
      border-radius: 4px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: #fca5a5;
      overflow-x: auto;
    }
    .pack-card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .pack-card:hover {
      border-color: #38bdf8;
    }
  </style>
</head>
<body>
  <header>
    <div class="header-left">
      <div class="logo-badge">AOS</div>
      <div>
        <h1>AI Behavior Control Plane</h1>
        <p class="hero-subtitle">Real-time guardrails and permanent memory for Cursor, Copilot, and Claude Code</p>
      </div>
    </div>
    <div class="header-right">
      <div class="status-pill">
        <div class="pulse-dot"></div>
        Protection Active
      </div>
      <button class="btn" onclick="openIngestModal()">Scan Codebase</button>
      <button class="btn" onclick="openModal('how-modal')">? How It Works</button>
      <button class="btn btn-primary" onclick="openAddModal()">+ Add Guardrail</button>
      <button class="btn" onclick="syncAllHarnesses()">Sync Harnesses</button>
    </div>
  </header>

  <div class="stats-row">
    <div class="stat-card">
      <div class="label">Active Guardrails</div>
      <div class="value" id="count-active">0</div>
      <div class="subtext" id="count-active-sub">Machine-enforced rules</div>
    </div>
    <div class="stat-card">
      <div class="label">Connected AI Tools</div>
      <div class="value" id="count-harnesses">0 / 5</div>
      <div class="subtext" id="count-harnesses-sub">Prompt targets and git hooks</div>
    </div>
    <div class="stat-card">
      <div class="label">Total Blocked Incidents</div>
      <div class="value" id="count-blocked" style="color: #f87171;">0</div>
      <div class="subtext">Prevented invalid diffs</div>
    </div>
    <div class="stat-card">
      <div class="label">Enforcement Mode</div>
      <div class="value" style="font-size: 18px; color: #38bdf8; margin-top: 8px;">Strict Pre-Commit</div>
      <div class="subtext">Deterministic diff rejection</div>
    </div>
  </div>

  <div class="tabs-nav">
    <button class="tab-btn active" id="tab-btn-rules" onclick="switchTab('tab-rules', this)">
      <span>Active Guardrails</span>
      <span class="tab-badge" id="tab-badge-rules">0</span>
      <span class="kbd-shortcut">1</span>
    </button>
    <button class="tab-btn" id="tab-btn-tools" onclick="switchTab('tab-tools', this)">
      <span>Connected AI Tools</span>
      <span class="tab-badge" id="tab-badge-tools">0</span>
      <span class="kbd-shortcut">2</span>
    </button>
    <button class="tab-btn" id="tab-btn-packs" onclick="switchTab('tab-packs', this)">
      <span>Rule Packs</span>
      <span class="tab-badge" id="tab-badge-packs">3</span>
      <span class="kbd-shortcut">3</span>
    </button>
    <button class="tab-btn" id="tab-btn-incidents" onclick="switchTab('tab-incidents', this)">
      <span>AI Incidents</span>
      <span class="tab-badge" id="tab-badge-incidents">0</span>
      <span class="kbd-shortcut">4</span>
    </button>
    <button class="tab-btn" id="tab-btn-inspector" onclick="switchTab('tab-inspector', this)">
      <span>Guardrail Inspector</span>
      <span class="kbd-shortcut">5</span>
    </button>
  </div>

  <!-- TAB 1: Guardrails -->
  <div id="tab-rules" class="tab-content active">
    <div class="toolbar">
      <div class="search-container">
        <input type="text" id="rule-search" class="search-input" placeholder="Filter guardrails by ID, statement, or scope..." oninput="filterRules()">
        <span class="search-kbd" title="Press / to search">/</span>
      </div>
      <div class="filter-group">
        <button class="filter-chip active" onclick="setFilter('all', this)">All</button>
        <button class="filter-chip" onclick="setFilter('active', this)">Active</button>
        <button class="filter-chip" onclick="setFilter('candidate', this)">Candidate</button>
        <button class="filter-chip" onclick="setFilter('archive', this)">Archive</button>
      </div>
    </div>
    <div class="rule-grid" id="rules-grid">
      <div style="color: var(--text-muted); padding: 20px;">Loading guardrails...</div>
    </div>
  </div>

  <!-- TAB 2: Connected AI Tools -->
  <div id="tab-tools" class="tab-content">
    <div class="sync-banner">
      <div class="sync-banner-text">
        <h3>Synchronize Substrate Invariants Across AI Tools</h3>
        <p>AOS compiles active repository invariants into configuration files read by local coding assistants and pre-commit hooks.</p>
      </div>
      <button class="btn btn-primary" onclick="syncAllHarnesses()">Sync All Tools Now</button>
    </div>
    <div class="tools-grid" id="tools-grid">
      <div style="color: var(--text-muted); padding: 20px;">Checking connected tools...</div>
    </div>
  </div>

  <!-- TAB 3: Rule Packs -->
  <div id="tab-packs" class="tab-content">
    <div class="sync-banner" style="margin-bottom: 24px;">
      <div class="sync-banner-text">
        <h3>Curated Invariant Rule Packs</h3>
        <p>1-click deploy enterprise security, clean architecture, and performance constraints into your repository substrate.</p>
      </div>
      <button class="btn btn-sm" onclick="loadPacks()">Refresh Packs</button>
    </div>
    <div id="packs-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
      <div style="color: var(--text-muted); padding: 20px;">Loading rule packs...</div>
    </div>
  </div>

  <!-- TAB 4: Incident Log -->
  <div id="tab-incidents" class="tab-content">
    <div class="toolbar">
      <p style="font-size: 13px; color: var(--text-muted);">Real-time ledger of AI mistake autopsies, peer critic rejections, and blocked commits.</p>
      <button class="btn btn-sm" onclick="loadIncidents()">Refresh Incidents</button>
    </div>
    <div class="incident-list" id="incidents-list">
      <div style="color: var(--text-muted); padding: 20px;">Loading incident log...</div>
    </div>
  </div>

  <!-- TAB 5: Guardrail Inspector & Tester -->
  <div id="tab-inspector" class="tab-content">
    <!-- Live Code & Diff Tester Sandbox -->
    <div class="inspector-box" style="margin-bottom: 24px;">
      <h3 style="font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 4px;">Live Guardrail &amp; Diff Enforcement Sandbox</h3>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 14px;">Simulate pre-commit barrier verification: test code snippets and patches against all active repository guardrails.</p>
      
      <div style="display: flex; gap: 12px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 260px;">
          <label style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); display: block; margin-bottom: 4px;">Target File Path</label>
          <input type="text" id="tester-path" class="inspector-input" style="width: 100%;" value="src/aos/sample.py" placeholder="e.g. src/aos/ui.py or lib/db.py">
        </div>
        <div style="padding-top: 18px; display: flex; gap: 8px; flex-wrap: wrap;">
          <button type="button" class="btn btn-sm" onclick="setTesterSample('em_dash')">Test Em-Dash Violation</button>
          <button type="button" class="btn btn-sm" onclick="setTesterSample('valid_python')">Test Valid Python Code</button>
        </div>
      </div>

      <div style="margin-bottom: 12px;">
        <label style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); display: block; margin-bottom: 4px;">Code Snippet / Diff Content</label>
        <textarea id="tester-content" class="form-textarea" style="font-family: var(--font-mono); font-size: 12.5px; min-height: 130px; line-height: 1.4; background: #090d16;" placeholder="# Paste code snippet or patch here to evaluate against active guardrails..."></textarea>
      </div>

      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn btn-primary" onclick="runContentTester()">Run Guardrail Check</button>
      </div>

      <div id="tester-verdict"></div>
    </div>

    <!-- Scope Path Inspector -->
    <div class="inspector-box">
      <h3 style="font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 6px;">Test File Path Guardrail Scope</h3>
      <p style="font-size: 13px; color: var(--text-muted);">Verify which invariants will constrain an AI agent when it edits a specific file path.</p>
      <div class="inspector-form">
        <input type="text" id="inspector-path" class="inspector-input" placeholder="e.g. src/aos/ui.py or tests/test_harness.py" value="src/aos/ui.py">
        <button class="btn btn-primary" onclick="runInspectorCheck()">Inspect Path</button>
      </div>
      <div style="margin-top: 12px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
        <span style="font-size: 12px; color: var(--text-muted);">Quick samples:</span>
        <button class="btn btn-sm" onclick="setInspectorPath('src/aos/ui.py')">src/aos/ui.py</button>
        <button class="btn btn-sm" onclick="setInspectorPath('src/aos/models.py')">src/aos/models.py</button>
        <button class="btn btn-sm" onclick="setInspectorPath('CLAUDE.md')">CLAUDE.md</button>
        <button class="btn btn-sm" onclick="setInspectorPath('AGENTS.md')">AGENTS.md</button>
      </div>
    </div>
    <div id="inspector-results"></div>
  </div>

  <!-- Modal: Add Guardrail -->
  <div class="modal-backdrop" id="add-modal">
    <div class="modal">
      <div class="modal-header">
        <div class="modal-title">Define New Repository Guardrail</div>
        <button type="button" class="modal-close-btn" onclick="closeModal('add-modal')" title="Close (Escape)">&times;</button>
      </div>
      <div class="modal-subtitle">Creates a persistent invariant rule in .agents/substrate/active/ enforced on AI agents.</div>
      
      <!-- 1-Click Guardrail Templates -->
      <div style="margin-bottom: 16px; padding: 12px; background: #090d16; border: 1px solid var(--border); border-radius: 8px;">
        <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); letter-spacing: 0.5px; display: block; margin-bottom: 8px;">1-Click Guardrail Templates</span>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button type="button" class="template-chip" onclick="applyGuardrailTemplate('sql_injection')">OWASP SQL Injection</button>
          <button type="button" class="template-chip" onclick="applyGuardrailTemplate('zero_em_dashes')">Zero Em-Dashes</button>
          <button type="button" class="template-chip" onclick="applyGuardrailTemplate('no_secrets')">No Hardcoded Secrets</button>
          <button type="button" class="template-chip" onclick="applyGuardrailTemplate('surgical_diff')">Surgical Diff (30 Lines)</button>
        </div>
      </div>

      <div id="modal-error" class="form-error" style="display: none;"></div>
      <form id="add-rule-form" onsubmit="submitNewRule(event)">
        <div class="form-group">
          <label>Rule Identifier</label>
          <input type="text" id="form-id" class="form-input" placeholder="e.g. no-unhandled-exceptions" required>
        </div>
        <div class="form-group">
          <label>Enforcement Action</label>
          <select id="form-enforcement" class="form-select">
            <option value="reject_diff">BLOCK (reject_diff): Strictly block diff in pre-commit</option>
            <option value="warn">WARN: Advisory warning in AI prompt</option>
            <option value="audit">AUDIT: Passive recording on blackboard</option>
          </select>
        </div>
        <div class="form-group">
          <label>Invariant Statement (What the AI must strictly obey)</label>
          <textarea id="form-statement" class="form-textarea" placeholder="e.g. All database queries must use prepared statements." required></textarea>
        </div>
        <div class="form-group">
          <label>Rationale (Why this constraint exists)</label>
          <textarea id="form-rationale" class="form-textarea" placeholder="e.g. Prevents SQL injection vulnerabilities and ensures audit compliance."></textarea>
        </div>
        <div class="form-group">
          <label>Scope Paths (Comma-separated glob patterns)</label>
          <input type="text" id="form-paths" class="form-input" placeholder="e.g. src/**/*.py, tests/**/*.py" value="**/*">
        </div>
        <div class="form-group">
          <label>Languages (Comma-separated, optional)</label>
          <input type="text" id="form-languages" class="form-input" placeholder="e.g. python, typescript">
        </div>
        <div class="modal-footer">
          <button type="button" class="btn" onclick="closeModal('add-modal')">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Guardrail</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal: View Raw Rule YAML -->
  <div class="modal-backdrop" id="yaml-modal">
    <div class="modal" style="max-width: 680px;">
      <div class="modal-header">
        <div class="modal-title" id="yaml-modal-title">Rule Definition YAML</div>
        <button type="button" class="modal-close-btn" onclick="closeModal('yaml-modal')" title="Close (Escape)">&times;</button>
      </div>
      <div class="modal-subtitle" id="yaml-modal-subtitle">Exact declarative substrate specification on disk.</div>
      <div style="position: relative; margin-bottom: 16px;">
        <pre id="yaml-modal-content" style="background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 14px; font-family: var(--font-mono); font-size: 12px; color: #e2e8f0; max-height: 380px; overflow: auto; white-space: pre;"></pre>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn" onclick="copyModalContent('yaml-modal-content', this)">Copy to Clipboard</button>
        <button type="button" class="btn btn-primary" onclick="closeModal('yaml-modal')">Close</button>
      </div>
    </div>
  </div>

  <!-- Modal: View Tool Config -->
  <div class="modal-backdrop" id="harness-modal">
    <div class="modal" style="max-width: 720px;">
      <div class="modal-header">
        <div class="modal-title" id="harness-modal-title">AI Tool Injected Instructions</div>
        <button type="button" class="modal-close-btn" onclick="closeModal('harness-modal')" title="Close (Escape)">&times;</button>
      </div>
      <div class="modal-subtitle" id="harness-modal-subtitle">Compiled system prompt configuration injected into AI agent.</div>
      <div style="position: relative; margin-bottom: 16px;">
        <pre id="harness-modal-content" style="background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 14px; font-family: var(--font-mono); font-size: 12px; color: #e2e8f0; max-height: 380px; overflow: auto; white-space: pre;"></pre>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn" onclick="copyModalContent('harness-modal-content', this)">Copy to Clipboard</button>
        <button type="button" class="btn btn-primary" onclick="closeModal('harness-modal')">Close</button>
      </div>
    </div>
  </div>

  <!-- Modal: How AOS Works -->
  <div class="modal-backdrop" id="how-modal">
    <div class="modal" style="max-width: 740px;">
      <div class="modal-header">
        <div class="modal-title">How AOS Controls AI Behavior: The 4 Pillars</div>
        <button type="button" class="modal-close-btn" onclick="closeModal('how-modal')" title="Close (Escape)">&times;</button>
      </div>
      <div class="modal-subtitle">Deterministic guardrails and permanent memory for autonomous coding agents.</div>
      
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px;">
        <div style="background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 16px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
            <span style="background: var(--primary-glow); color: var(--primary); font-weight: 800; font-size: 12px; padding: 2px 8px; border-radius: 4px;">PILLAR 1</span>
            <strong style="color: #fff; font-size: 13.5px;">Invariant Guardrails</strong>
          </div>
          <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.4;">
            Declarative repository rules stored in <code>.agents/substrate/active/*.yaml</code>. Machine-readable, versioned constraints that define what code an AI agent is forbidden from producing.
          </p>
        </div>

        <div style="background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 16px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
            <span style="background: rgba(16, 185, 129, 0.15); color: #34d399; font-weight: 800; font-size: 12px; padding: 2px 8px; border-radius: 4px;">PILLAR 2</span>
            <strong style="color: #fff; font-size: 13.5px;">Multi-Harness Sync</strong>
          </div>
          <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.4;">
            Active invariants are compiled into configuration files across Cursor (<code>.cursorrules</code>), Claude Code (<code>CLAUDE.md</code>), Windsurf (<code>.windsurfrules</code>), and Copilot Chat.
          </p>
        </div>

        <div style="background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 16px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
            <span style="background: rgba(239, 68, 68, 0.15); color: #f87171; font-weight: 800; font-size: 12px; padding: 2px 8px; border-radius: 4px;">PILLAR 3</span>
            <strong style="color: #fff; font-size: 13.5px;">Pre-Commit Barrier</strong>
          </div>
          <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.4;">
            A deterministic git pre-commit hook intercepts proposed diffs before commit. Violations (e.g. em-dashes, blast radius, secrets) strictly block the commit with zero ambiguity.
          </p>
        </div>

        <div style="background: #090d16; border: 1px solid var(--border); border-radius: 8px; padding: 16px;">
          <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 8px;">
            <span style="background: rgba(147, 51, 234, 0.15); color: #c084fc; font-weight: 800; font-size: 12px; padding: 2px 8px; border-radius: 4px;">PILLAR 4</span>
            <strong style="color: #fff; font-size: 13.5px;">Autopsy Loop</strong>
          </div>
          <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.4;">
            When an AI causes an incident, AOS records a structured autopsy on the blackboard and synthesizes candidate invariants to ensure the fleet never repeats the same mistake.
          </p>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-primary" onclick="closeModal('how-modal')">Got It</button>
      </div>
    </div>
  </div>

  <!-- Modal: Ingest Codebase Conventions -->
  <div class="modal-backdrop" id="ingest-modal">
    <div class="modal" style="max-width: 760px;">
      <div class="modal-header">
        <div class="modal-title">Autonomous Codebase Ingestion</div>
        <button type="button" class="modal-close-btn" onclick="closeModal('ingest-modal')" title="Close (Escape)">&times;</button>
      </div>
      <div class="modal-subtitle">Analyzes package configs, linters, and team instructions to synthesize tailored guardrails.</div>
      <div id="ingest-modal-body" style="margin-top: 14px; min-height: 180px;">
        <div style="text-align: center; padding: 30px; color: var(--text-muted);">
          Scanning repository architecture and team instructions...
        </div>
      </div>
      <div class="modal-footer" id="ingest-modal-footer">
        <button type="button" class="btn" onclick="closeModal('ingest-modal')">Close</button>
        <button type="button" class="btn btn-primary" id="ingest-apply-btn" onclick="applyIngestedRules()" style="display: none;">Activate Tailored Guardrails</button>
      </div>
    </div>
  </div>

  <div id="toast-container" class="toast-container" aria-live="polite"></div>
  <div id="toast" style="display: none;"></div>

  <script>
    let allRules = [];
    let currentFilter = 'all';

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      if (!container) return;

      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;

      const iconSpan = document.createElement('span');
      iconSpan.className = 'toast-icon';
      iconSpan.innerText = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');

      const msgSpan = document.createElement('span');
      msgSpan.className = 'toast-msg';
      msgSpan.innerText = message;

      toast.appendChild(iconSpan);
      toast.appendChild(msgSpan);
      container.appendChild(toast);

      const legacyToast = document.getElementById('toast');
      if (legacyToast) legacyToast.innerText = message;

      requestAnimationFrame(() => {
        toast.classList.add('toast-visible');
      });

      setTimeout(() => {
        toast.classList.remove('toast-visible');
        setTimeout(() => {
          if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
      }, 3000);
    }

    function debounce(fn, delay = 200) {
      let timer = null;
      return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
      };
    }

    const debouncedFilterRules = debounce(() => {
      renderRules();
    }, 200);

    function filterRules() {
      debouncedFilterRules();
    }

    function switchTab(tabId, el) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
      document.getElementById(tabId).classList.add('active');
      if (tabId === 'tab-tools') loadHarnesses();
      if (tabId === 'tab-packs') loadPacks();
      if (tabId === 'tab-incidents') loadIncidents();
    }

    function setFilter(filter, el) {
      currentFilter = filter;
      document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      el.classList.add('active');
      renderRules();
    }

    function updateTabBadges(rulesCount, toolsCount, incidentsCount) {
      if (rulesCount !== undefined && rulesCount !== null) {
        const badge = document.getElementById('tab-badge-rules');
        if (badge) badge.innerText = rulesCount;
      }
      if (toolsCount !== undefined && toolsCount !== null) {
        const badge = document.getElementById('tab-badge-tools');
        if (badge) badge.innerText = toolsCount;
      }
      if (incidentsCount !== undefined && incidentsCount !== null) {
        const badge = document.getElementById('tab-badge-incidents');
        if (badge) badge.innerText = incidentsCount;
      }
    }

    async function loadOverview() {
      try {
        const res = await fetch('/api/overview');
        const data = await res.json();
        const activeCount = data.active_rules || 0;
        const harnessesCount = data.connected_harnesses || 0;
        const blockedCount = data.total_blocked_incidents || 0;

        document.getElementById('count-active').innerText = activeCount;
        document.getElementById('count-active-sub').innerText = `${data.candidate_rules || 0} candidate, ${data.archived_rules || 0} archived`;
        document.getElementById('count-harnesses').innerText = `${harnessesCount} / ${data.total_harnesses || 5}`;
        document.getElementById('count-blocked').innerText = blockedCount;

        updateTabBadges(activeCount, harnessesCount, blockedCount);
      } catch (err) {
        console.error('Failed to load overview:', err);
      }
    }

    async function loadRules() {
      try {
        const res = await fetch('/api/rules');
        allRules = await res.json();
        const activeCount = allRules.filter(r => r.status === 'active').length;
        const badge = document.getElementById('tab-badge-rules');
        if (badge) badge.innerText = activeCount;
        renderRules();
      } catch (err) {
        console.error('Failed to load rules:', err);
      }
    }

    const expandedRuleIds = new Set();

    function toggleRuleExpand(ruleId, event) {
      if (event.target.closest('.switch') || event.target.closest('button') || event.target.closest('a')) {
        return;
      }
      if (expandedRuleIds.has(ruleId)) {
        expandedRuleIds.delete(ruleId);
      } else {
        expandedRuleIds.add(ruleId);
      }
      const card = document.getElementById(`rule-card-${ruleId}`);
      const details = document.getElementById(`rule-details-${ruleId}`);
      const cue = document.getElementById(`expand-cue-${ruleId}`);
      if (card && details && cue) {
        const isExp = expandedRuleIds.has(ruleId);
        card.classList.toggle('expanded', isExp);
        details.style.display = isExp ? 'block' : 'none';
        cue.innerText = isExp ? '▲ Collapse metadata' : '▼ Click to inspect metadata';
      }
    }

    function renderRules() {
      const q = (document.getElementById('rule-search').value || '').toLowerCase();
      const filtered = allRules.filter(r => {
        const matchesFilter = currentFilter === 'all' || r.status === currentFilter;
        const matchesQuery = !q ||
          r.id.toLowerCase().includes(q) ||
          (r.invariant.statement || '').toLowerCase().includes(q) ||
          (r.scope.paths || []).some(p => p.toLowerCase().includes(q));
        return matchesFilter && matchesQuery;
      });

      const grid = document.getElementById('rules-grid');
      if (!filtered.length) {
        grid.innerHTML = '<div style="color: var(--text-muted); padding: 24px; grid-column: span 2;">No guardrails matching the filter.</div>';
        return;
      }

      grid.innerHTML = filtered.map(r => {
        const isBlock = r.invariant.enforcement === 'reject_diff';
        const enfBadge = isBlock
          ? '<span class="badge badge-block">BLOCK (reject_diff)</span>'
          : '<span class="badge badge-warn">WARN</span>';

        let statusBadge = '<span class="badge badge-active">ACTIVE</span>';
        if (r.status === 'candidate') statusBadge = '<span class="badge badge-candidate">CANDIDATE</span>';
        if (r.status === 'archive') statusBadge = '<span class="badge badge-archive">ARCHIVED</span>';

        const paths = (r.scope.paths || []).map(p => `<span class="chip">${escapeHtml(p)}</span>`).join(' ') || '<span class="chip">all</span>';
        const isChecked = r.status === 'active' ? 'checked' : '';
        const isExpanded = expandedRuleIds.has(r.id);
        const prov = r.provenance || {};

        return `
          <div class="rule-card ${isExpanded ? 'expanded' : ''}" id="rule-card-${escapeHtml(r.id)}" onclick="toggleRuleExpand('${escapeHtml(r.id)}', event)">
            <div>
              <div class="rule-header">
                <div class="rule-title-group">
                  <span class="rule-id">${escapeHtml(r.id)}</span>
                  ${enfBadge}
                  ${statusBadge}
                </div>
                <div class="switch-wrap" onclick="event.stopPropagation()">
                  <label class="switch" title="Toggle Active / Archive status" onclick="event.stopPropagation()">
                    <input type="checkbox" ${isChecked} onchange="toggleRuleStatus('${escapeHtml(r.id)}')" onclick="event.stopPropagation()">
                    <span class="slider"></span>
                  </label>
                </div>
              </div>
              <div class="rule-statement">${escapeHtml(r.invariant.statement)}</div>
              <div class="rule-rationale">Why: ${escapeHtml(r.invariant.rationale)}</div>
            </div>
            <div>
              <div class="rule-meta">
                <span>Scope:</span> ${paths}
                ${r.invariant.max_blast_radius_lines ? `<span class="chip">max diff: ${r.invariant.max_blast_radius_lines} lines</span>` : ''}
                ${prov.trigger_count ? `<span class="chip" style="color: #f87171;">triggered: ${prov.trigger_count}x</span>` : ''}
              </div>
              <div class="rule-details" id="rule-details-${escapeHtml(r.id)}" style="${isExpanded ? 'display: block;' : 'display: none;'}">
                <div class="rule-details-grid">
                  <div class="detail-item">
                    <span class="detail-label">Inscribing Agent</span>
                    <span class="detail-value">${escapeHtml(prov.inscribing_agent || 'unknown')}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Git Commit Origin</span>
                    <span class="detail-value mono">${escapeHtml(prov.git_commit || 'HEAD')}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Trigger Count</span>
                    <span class="detail-value">${prov.trigger_count || 0}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Last Verified</span>
                    <span class="detail-value">${escapeHtml(prov.last_verified_at || 'Never')}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Created At</span>
                    <span class="detail-value">${escapeHtml(prov.created_at || 'Unknown')}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">Incident ID</span>
                    <span class="detail-value mono">${escapeHtml(prov.incident_id || 'manual')}</span>
                  </div>
                </div>
              </div>
              <div class="rule-card-footer" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                <button type="button" class="btn btn-sm" onclick="viewRuleYaml('${escapeHtml(r.id)}', event)" style="padding: 3px 8px; font-size: 11px;">View YAML</button>
                <span class="expand-cue" id="expand-cue-${escapeHtml(r.id)}">${isExpanded ? '▲ Collapse metadata' : '▼ Click to inspect metadata'}</span>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    async function toggleRuleStatus(ruleId) {
      try {
        const res = await fetch('/api/rules/toggle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rule_id: ruleId }),
        });
        const data = await res.json();
        if (res.ok) {
          showToast(`Guardrail ${ruleId} toggled to ${data.new_status}`, 'success');
          await loadRules();
          await loadOverview();
        } else {
          showToast(`Error: ${data.error || 'Failed to toggle rule'}`, 'error');
          await loadRules();
        }
      } catch (err) {
        console.error(err);
        showToast('Network error while toggling rule', 'error');
      }
    }

    function showModalError(msg) {
      const err = document.getElementById('modal-error');
      if (err) {
        err.innerText = msg;
        err.style.display = 'flex';
      }
    }

    function clearModalErrors() {
      const err = document.getElementById('modal-error');
      if (err) {
        err.innerText = '';
        err.style.display = 'none';
      }
      document.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
    }

    function openModal(modalId) {
      if (modalId === 'add-modal') return openAddModal();
      const modal = document.getElementById(modalId);
      if (!modal) return;
      modal.style.display = 'flex';
      requestAnimationFrame(() => {
        modal.classList.add('open');
      });
    }

    function closeModal(modalId) {
      if (modalId === 'add-modal') return closeAddModal();
      const modal = document.getElementById(modalId);
      if (!modal) return;
      modal.classList.remove('open');
      setTimeout(() => {
        if (!modal.classList.contains('open')) {
          modal.style.display = 'none';
        }
      }, 250);
    }

    function applyGuardrailTemplate(name) {
      const idInput = document.getElementById('form-id');
      const stInput = document.getElementById('form-statement');
      const ratInput = document.getElementById('form-rationale');
      const pathsInput = document.getElementById('form-paths');
      const langInput = document.getElementById('form-languages');
      const enfSelect = document.getElementById('form-enforcement');

      if (name === 'sql_injection') {
        idInput.value = 'sec-sql-injection';
        stInput.value = 'SQL queries must use parameterized bind variables, never raw string interpolation or concatenation.';
        ratInput.value = 'Direct string interpolation in SQL strings creates critical SQL injection vulnerabilities.';
        pathsInput.value = 'src/**/*.py';
        langInput.value = 'python';
        enfSelect.value = 'reject_diff';
      } else if (name === 'zero_em_dashes') {
        idInput.value = 'no-em-dashes';
        stInput.value = 'Zero em dashes in all prose, documentation, commit messages, and comments.';
        ratInput.value = 'Enforce standard punctuation across team.';
        pathsInput.value = '**/*';
        langInput.value = '';
        enfSelect.value = 'reject_diff';
      } else if (name === 'no_secrets') {
        idInput.value = 'no-hardcoded-secrets';
        stInput.value = 'Never commit API keys, private keys, or passwords. Use environment variables.';
        ratInput.value = 'Hardcoded credentials lead to catastrophic security compromise.';
        pathsInput.value = '**/*';
        langInput.value = '';
        enfSelect.value = 'reject_diff';
      } else if (name === 'surgical_diff') {
        idInput.value = 'surgical-diff-limit';
        stInput.value = 'Contiguous patch must not exceed 30 lines without technical justification.';
        ratInput.value = 'Maintain surgical blast radius and high review fidelity.';
        pathsInput.value = '**/*';
        langInput.value = '';
        enfSelect.value = 'reject_diff';
      }
      showToast('Template applied: ' + name, 'info');
    }

    function openAddModal() {
      const modal = document.getElementById('add-modal');
      clearModalErrors();
      modal.style.display = 'flex';
      requestAnimationFrame(() => {
        modal.classList.add('open');
      });
      setTimeout(() => {
        const idInput = document.getElementById('form-id');
        if (idInput) idInput.focus();
      }, 50);
    }

    function closeAddModal() {
      const modal = document.getElementById('add-modal');
      modal.classList.remove('open');
      setTimeout(() => {
        if (!modal.classList.contains('open')) {
          modal.style.display = 'none';
        }
      }, 250);
      const form = document.getElementById('add-rule-form');
      if (form) form.reset();
      clearModalErrors();
    }

    async function submitNewRule(evt) {
      evt.preventDefault();
      clearModalErrors();

      const idInput = document.getElementById('form-id');
      const statementInput = document.getElementById('form-statement');
      const ruleId = idInput.value.trim();
      const statement = statementInput.value.trim();

      if (!ruleId) {
        idInput.classList.add('input-error');
        showModalError('Rule Identifier is required.');
        idInput.focus();
        return;
      }
      if (!statement) {
        statementInput.classList.add('input-error');
        showModalError('Invariant Statement is required.');
        statementInput.focus();
        return;
      }

      const payload = {
        id: ruleId,
        enforcement: document.getElementById('form-enforcement').value,
        statement: statement,
        rationale: document.getElementById('form-rationale').value.trim(),
        paths: document.getElementById('form-paths').value.trim(),
        languages: document.getElementById('form-languages').value.trim(),
      };

      try {
        const res = await fetch('/api/rules/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (res.ok) {
          closeAddModal();
          showToast(`Guardrail ${payload.id} created successfully!`, 'success');
          await loadRules();
          await loadOverview();
        } else {
          const errMsg = data.error || (data.details ? JSON.stringify(data.details) : 'Failed to create guardrail.');
          showModalError(`Failed to create rule: ${errMsg}`);
          showToast(`Failed to create rule: ${errMsg}`, 'error');
        }
      } catch (err) {
        console.error(err);
        showModalError('Network error while creating guardrail.');
        showToast('Network error while creating guardrail.', 'error');
      }
    }

    async function loadHarnesses() {
      try {
        const res = await fetch('/api/harnesses');
        const data = await res.json();
        const list = Array.isArray(data) ? data : (data.harnesses || []);
        const connectedCount = list.filter(h => h.exists).length;
        const badge = document.getElementById('tab-badge-tools');
        if (badge) badge.innerText = connectedCount;

        const grid = document.getElementById('tools-grid');

        grid.innerHTML = list.map(h => {
          const statusBadge = h.exists
            ? '<span class="badge badge-active">CONNECTED</span>'
            : '<span class="badge badge-archive">MISSING / UNCONFIGURED</span>';

          const actionBtn = h.id === 'git_hook'
            ? `<button class="btn btn-sm" onclick="installGitHook()">${h.exists ? 'Re-install Hook' : 'Install Git Hook'}</button>`
            : `<button class="btn btn-sm" onclick="syncAllHarnesses()">Sync Instructions</button>`;

          return `
            <div class="tool-card">
              <div>
                <div class="tool-header">
                  <span class="tool-name">${h.name}</span>
                  ${statusBadge}
                </div>
                <div class="tool-path">${h.path}</div>
                <div class="tool-desc">${h.description}</div>
              </div>
              <div style="margin-top: 14px; display: flex; justify-content: flex-end; gap: 8px;">
                <button class="btn btn-sm" onclick="viewHarnessConfig('${h.id}', '${escapeHtml(h.name)}', '${escapeHtml(h.path)}')">View Config</button>
                ${actionBtn}
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        console.error('Failed to load harnesses:', err);
      }
    }

    async function syncAllHarnesses() {
      try {
        const res = await fetch('/api/harnesses/sync', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          showToast(`Synchronized ${data.count || data.synced.length} tool configurations.`, 'success');
          await loadHarnesses();
          await loadOverview();
        } else {
          showToast('Failed to sync harnesses', 'error');
        }
      } catch (err) {
        console.error(err);
        showToast('Network error during sync', 'error');
      }
    }

    async function installGitHook() {
      try {
        const res = await fetch('/api/harnesses/hook/install', { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
          showToast('Git pre-commit hook installed successfully.', 'success');
          await loadHarnesses();
          await loadOverview();
        } else {
          showToast(`Hook install failed: ${data.error}`, 'error');
        }
      } catch (err) {
        console.error(err);
        showToast('Failed to install hook', 'error');
      }
    }

    async function loadIncidents() {
      try {
        const res = await fetch('/api/incidents');
        const list = await res.json();
        const badge = document.getElementById('tab-badge-incidents');
        if (badge) badge.innerText = list.length;
        const container = document.getElementById('incidents-list');

        if (!list.length) {
          container.innerHTML = `
            <div class="incident-card" style="text-align: center; color: var(--text-muted); padding: 32px;">
              No violations or autopsies recorded yet. All active invariants verified clean.
            </div>
          `;
          return;
        }

        container.innerHTML = list.map(ev => {
          const isAutopsy = ev.type === 'AUTOPSY_RECORD';
          const p = ev.payload || {};
          const badgeCls = isAutopsy ? 'badge-candidate' : 'badge-block';
          const typeLabel = isAutopsy ? 'FAILURE AUTOPSY' : 'PEER CRITIQUE';

          return `
            <div class="incident-card">
              <div class="incident-header">
                <div style="display: flex; gap: 8px; align-items: center;">
                  <span class="badge ${badgeCls}">${typeLabel}</span>
                  <span style="font-family: var(--font-mono); font-size: 12px; color: #cbd5e1;">${ev.event_id || ''}</span>
                  <span style="font-size: 12px; color: var(--text-muted); font-weight: 500;">by ${ev.sender || 'auditor'}</span>
                </div>
                <span style="font-size: 11px; color: var(--text-muted);">${ev.timestamp || ''}</span>
              </div>
              <div style="font-size: 13.5px; color: #e2e8f0; margin-top: 6px;">
                ${isAutopsy ? `Captured incident on rule <code>${p.rule_id || ''}</code>: "${p.statement || ''}"` : `Auditor verdict: <strong>${p.verdict || ''}</strong>. ${p.message || ''}`}
              </div>
              <details style="margin-top: 10px;">
                <summary style="font-size: 11px; color: var(--text-muted); cursor: pointer;">Raw Blackboard Event</summary>
                <pre style="margin-top: 6px; background: #090d16; border: 1px solid var(--border); padding: 10px; border-radius: 6px; font-family: var(--font-mono); font-size: 11px; overflow-x: auto; color: #94a3b8;">${JSON.stringify(ev, null, 2)}</pre>
              </details>
            </div>
          `;
        }).join('');
      } catch (err) {
        console.error('Failed to load incidents:', err);
      }
    }

    function setInspectorPath(p) {
      document.getElementById('inspector-path').value = p;
      runInspectorCheck();
    }

    async function runInspectorCheck() {
      const pathVal = document.getElementById('inspector-path').value.trim();
      if (!pathVal) return;

      const resDiv = document.getElementById('inspector-results');
      resDiv.innerHTML = '<div style="color: var(--text-muted); padding: 12px;">Evaluating matching rules...</div>';

      try {
        const res = await fetch('/api/check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_path: pathVal }),
        });
        const data = await res.json();
        const matches = data.matches || [];

        if (!matches.length) {
          resDiv.innerHTML = `
            <div style="background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; padding: 20px; color: var(--text-muted);">
              No active guardrails restrict <code>${pathVal}</code>.
            </div>
          `;
          return;
        }

        resDiv.innerHTML = `
          <div style="margin-bottom: 12px; font-size: 13px; color: var(--text-muted);">
            Found <strong>${matches.length}</strong> active guardrail(s) restricting <code>${pathVal}</code>:
          </div>
          <div class="rule-grid">
            ${matches.map(m => `
              <div class="rule-card">
                <div>
                  <div class="rule-header">
                    <span class="rule-id">${m.id}</span>
                    <span class="badge ${m.invariant.enforcement === 'reject_diff' ? 'badge-block' : 'badge-warn'}">
                      ${m.invariant.enforcement}
                    </span>
                  </div>
                  <div class="rule-statement">${m.invariant.statement}</div>
                  <div class="rule-rationale">Why: ${m.invariant.rationale}</div>
                </div>
                <div class="rule-meta">
                  Scope: ${(m.scope.paths || []).map(p => `<span class="chip">${p}</span>`).join(' ')}
                </div>
              </div>
            `).join('')}
          </div>
        `;
      } catch (err) {
        console.error(err);
        resDiv.innerHTML = '<div style="color: #f87171;">Failed to execute path check.</div>';
      }
    }

    // Live Code & Diff Tester execution
    function setTesterSample(type) {
      const pathEl = document.getElementById('tester-path');
      const contentEl = document.getElementById('tester-content');
      if (type === 'em_dash') {
        pathEl.value = 'src/aos/sample.py';
        contentEl.value = [
          '# Critical logic with forbidden punctuation: ' + String.fromCharCode(8212) + ' causes rejection',
          'def compute():',
          '    return True',
          ''
        ].join(String.fromCharCode(10));
        runContentTester();
      } else if (type === 'valid_python') {
        pathEl.value = 'src/aos/sample.py';
        contentEl.value = [
          'def compute_metrics(values: list[float]) -> float:',
          '    # Compute mean metrics cleanly without violations.',
          '    if not values:',
          '        return 0.0',
          '    return sum(values) / len(values)',
          ''
        ].join(String.fromCharCode(10));
        runContentTester();
      }
    }

    async function runContentTester() {
      const pathVal = (document.getElementById('tester-path').value || '').trim() || 'sample.py';
      const contentVal = document.getElementById('tester-content').value || '';
      const verdictDiv = document.getElementById('tester-verdict');
      verdictDiv.innerHTML = '<div style="color: var(--text-muted); padding: 10px;">Evaluating against active guardrails...</div>';

      try {
        const res = await fetch('/api/check-content', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_path: pathVal, content: contentVal }),
        });
        const data = await res.json();
        const allowed = data.allowed;
        const violations = data.violations || [];
        const matchingCount = data.matching_rules_count || 0;

        if (allowed) {
          verdictDiv.innerHTML = `
            <div class="verdict-banner verdict-allowed">
              <div class="verdict-header">
                <span class="verdict-icon">&#x2713;</span>
                <div>
                  <div class="verdict-title">ALLOWED: Code complies with all active guardrails.</div>
                  <div class="verdict-subtitle">No invariant violations detected across ${matchingCount} active matching rule(s).</div>
                </div>
              </div>
            </div>
          `;
        } else {
          const firstId = violations.length > 0 ? violations[0].rule_id : 'active-guardrail';
          verdictDiv.innerHTML = `
            <div class="verdict-banner verdict-blocked">
              <div class="verdict-header">
                <span class="verdict-icon">&#x2715;</span>
                <div>
                  <div class="verdict-title">BLOCKED: Diff rejected by repository guardrail [${escapeHtml(firstId)}]</div>
                  <div class="verdict-subtitle">${violations.length} violation(s) intercepted by pre-commit barrier.</div>
                </div>
              </div>
              <div style="margin-top: 14px; display: flex; flex-direction: column; gap: 10px;">
                ${violations.map(v => `
                  <div class="violation-item">
                    <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 6px; flex-wrap: wrap;">
                      <span class="badge badge-block">${escapeHtml(v.rule_id)}</span>
                      ${v.line_number ? `<span class="chip">Line ${v.line_number}</span>` : ''}
                      <span style="font-size: 12px; color: #f87171; font-weight: 600;">${escapeHtml(v.message)}</span>
                    </div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">
                      <strong>Invariant:</strong> ${escapeHtml(v.statement)}
                    </div>
                    ${v.snippet ? `<pre class="violation-snippet"><code>${escapeHtml(v.snippet)}</code></pre>` : ''}
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }
      } catch (err) {
        console.error(err);
        verdictDiv.innerHTML = '<div style="color: #f87171;">Failed to evaluate code content.</div>';
      }
    }

    // View Raw Rule YAML
    async function viewRuleYaml(ruleId, event) {
      if (event) event.stopPropagation();
      openModal('yaml-modal');
      document.getElementById('yaml-modal-title').innerText = `Rule Definition: ${ruleId}`;
      const codeEl = document.getElementById('yaml-modal-content');
      codeEl.innerText = 'Loading YAML...';
      try {
        const res = await fetch(`/api/rules/${encodeURIComponent(ruleId)}/yaml`);
        if (!res.ok) {
          codeEl.innerText = `Error loading rule YAML: ${res.statusText}`;
          return;
        }
        const data = await res.json();
        codeEl.innerText = data.yaml || '';
      } catch (err) {
        codeEl.innerText = `Network error: ${err}`;
      }
    }

    // View Tool Harness Config
    async function viewHarnessConfig(toolId, toolName, toolPath) {
      openModal('harness-modal');
      document.getElementById('harness-modal-title').innerText = `Tool Configuration: ${toolName}`;
      document.getElementById('harness-modal-subtitle').innerText = `Target file: ${toolPath}`;
      const codeEl = document.getElementById('harness-modal-content');
      codeEl.innerText = 'Loading configuration...';
      try {
        const res = await fetch(`/api/harnesses/view?id=${encodeURIComponent(toolId)}`);
        if (!res.ok) {
          codeEl.innerText = `Error loading tool configuration: ${res.statusText}`;
          return;
        }
        const data = await res.json();
        codeEl.innerText = data.content || '# No instructions generated.';
      } catch (err) {
        codeEl.innerText = `Network error: ${err}`;
      }
    }

    // Copy modal content to clipboard
    async function copyModalContent(elementId, btn) {
      const el = document.getElementById(elementId);
      if (!el) return;
      const text = el.innerText || el.textContent || '';
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          const ta = document.createElement('textarea');
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        const orig = btn.innerText;
        btn.innerText = 'Copied!';
        showToast('Copied to clipboard!', 'success');
        setTimeout(() => { btn.innerText = orig; }, 2000);
      } catch (err) {
        showToast('Failed to copy to clipboard', 'error');
      }
    }

    // Rule Packs
    async function loadPacks() {
      const grid = document.getElementById('packs-grid');
      if (!grid) return;
      try {
        const res = await fetch('/api/packs');
        const packs = await res.json();
        const list = Array.isArray(packs) ? packs : (packs.packs || []);
        
        grid.innerHTML = list.map(p => {
          const isInstalled = p.installed;
          const catBadge = p.category === 'SECURITY'
            ? '<span class="badge badge-block">SECURITY</span>'
            : (p.category === 'ARCHITECTURE' ? '<span class="badge badge-warn">ARCHITECTURE</span>' : '<span class="badge badge-active">PERFORMANCE</span>');
          
          const btnText = isInstalled ? 'Re-install Pack' : 'Install Pack';
          const btnClass = isInstalled ? 'btn btn-sm' : 'btn btn-primary btn-sm';

          return `
            <div class="pack-card">
              <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                  <h4 style="font-size: 15px; font-weight: 700; color: #fff;">${escapeHtml(p.title)}</h4>
                  ${catBadge}
                </div>
                <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 12px;">${escapeHtml(p.description)}</p>
                <div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">
                  Included Rules (${p.rule_count})
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px;">
                  ${(p.rules || []).map(r => `
                    <div style="background: #090d16; border: 1px solid var(--border); border-radius: 4px; padding: 6px 10px;">
                      <div style="font-family: var(--font-mono); font-size: 11px; color: var(--primary); font-weight: 700;">${escapeHtml(r.id)}</div>
                      <div style="font-size: 11.5px; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(r.statement)}</div>
                    </div>
                  `).join('')}
                </div>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border);">
                <span style="font-size: 11px; color: ${isInstalled ? '#34d399' : 'var(--text-muted)'}; font-weight: 600;">
                  ${isInstalled ? '✓ Pack Installed' : 'Not installed'}
                </span>
                <button class="${btnClass}" onclick="installRulePack('${escapeHtml(p.name)}', this)">${btnText}</button>
              </div>
            </div>
          `;
        }).join('');
      } catch (err) {
        grid.innerHTML = '<div style="color: #f87171; padding: 20px;">Failed to load packs.</div>';
      }
    }

    async function installRulePack(packName, btn) {
      const orig = btn ? btn.innerText : '';
      if (btn) btn.innerText = 'Installing...';
      try {
        const res = await fetch('/api/packs/install', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ pack_name: packName })
        });
        const data = await res.json();
        if (res.ok) {
          showToast(data.message || `Pack '${packName}' installed!`, 'success');
          await loadPacks();
          await loadRules();
          await loadOverview();
        } else {
          showToast(`Error: ${data.error || 'Failed to install pack'}`, 'error');
          if (btn) btn.innerText = orig;
        }
      } catch (err) {
        showToast('Network error while installing pack', 'error');
        if (btn) btn.innerText = orig;
      }
    }

    async function openIngestModal() {
      openModal('ingest-modal');
      const body = document.getElementById('ingest-modal-body');
      const applyBtn = document.getElementById('ingest-apply-btn');
      if (applyBtn) applyBtn.style.display = 'none';
      body.innerHTML = '<div style="text-align: center; padding: 30px; color: var(--text-muted);"><span class="pulse-dot" style="display: inline-block; margin-right: 8px;"></span>Scanning repository architecture and team instructions...</div>';
      try {
        const res = await fetch('/api/ingest/scan');
        if (!res.ok) {
          body.innerHTML = '<div style="color: #f87171; padding: 20px;">Failed to scan codebase: ' + escapeHtml(res.statusText) + '</div>';
          return;
        }
        const data = await res.json();
        renderIngestResults(data, body, applyBtn);
      } catch (err) {
        body.innerHTML = '<div style="color: #f87171; padding: 20px;">Error scanning codebase: ' + escapeHtml(err.message || err) + '</div>';
      }
    }

    function renderIngestResults(data, body, applyBtn) {
      const langs = (data.detected_languages || []).map(l => `<span class="chip">${escapeHtml(l)}</span>`).join(' ') || '<span class="chip">generic</span>';
      const frameworks = (data.detected_frameworks || []).map(f => `<span class="chip">${escapeHtml(f)}</span>`).join(' ') || '<span class="chip">standard</span>';
      const configs = (data.config_files || []).map(c => `<span class="chip">${escapeHtml(c)}</span>`).join(' ') || '<span class="chip">none</span>';
      const instrs = (data.instruction_files || []).map(i => `<span class="chip">${escapeHtml(i)}</span>`).join(' ') || '<span class="chip">none</span>';
      const rules = data.synthesized_rules || [];
      let rulesHtml = '<div style="color: var(--text-muted); padding: 12px 0; font-size: 12.5px;">No new unapplied conventions detected. Your guardrails are already synchronized.</div>';
      if (rules.length > 0) {
        if (applyBtn) {
          applyBtn.style.display = 'inline-block';
          applyBtn.innerText = `Activate ${rules.length} Tailored Guardrail(s)`;
        }
        rulesHtml = '<div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); margin: 16px 0 8px 0;">Synthesized Guardrails (' + rules.length + ')</div>' +
          '<div style="display: flex; flex-direction: column; gap: 8px; max-height: 240px; overflow-y: auto;">' +
          rules.map(r => '<div style="background: #090d16; border: 1px solid var(--border); border-radius: 6px; padding: 10px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;"><span style="font-family: var(--font-mono); font-size: 11.5px; font-weight: 700; color: var(--primary);">' + escapeHtml(r.id) + '</span><span class="badge badge-block">' + escapeHtml(r.enforcement || 'reject_diff') + '</span></div><div style="font-size: 12px; color: #e2e8f0; margin-bottom: 4px;">' + escapeHtml(r.statement) + '</div><div style="font-size: 11px; color: var(--text-muted);">Why: ' + escapeHtml(r.rationale) + '</div></div>').join('') +
          '</div>';
      }
      body.innerHTML = '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;"><div style="background: #090d16; border: 1px solid var(--border); border-radius: 6px; padding: 10px;"><div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">Tech Stack</div><div>' + langs + ' ' + frameworks + '</div></div><div style="background: #090d16; border: 1px solid var(--border); border-radius: 6px; padding: 10px;"><div style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">Discovered Inputs</div><div style="display: flex; flex-wrap: gap: 4px;">' + configs + ' ' + instrs + '</div></div></div>' + rulesHtml;
    }

    async function applyIngestedRules() {
      const btn = document.getElementById('ingest-apply-btn');
      if (btn) btn.innerText = 'Activating...';
      try {
        const res = await fetch('/api/ingest/apply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ promote: true })
        });
        const data = await res.json();
        if (res.ok) {
          closeModal('ingest-modal');
          showToast(data.message || 'Tailored guardrails activated successfully!', 'success');
          await loadRules();
          await loadOverview();
        } else {
          showToast('Failed: ' + (data.error || 'Activation failed'), 'error');
          if (btn) btn.innerText = 'Activate Tailored Guardrails';
        }
      } catch (err) {
        showToast('Network error while activating guardrails.', 'error');
        if (btn) btn.innerText = 'Activate Tailored Guardrails';
      }
    }

    // Modal click-outside listener
    ['add-modal', 'yaml-modal', 'harness-modal', 'how-modal', 'ingest-modal'].forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.addEventListener('click', (e) => {
          if (e.target === el) closeModal(id);
        });
      }
    });

    // Global keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        ['add-modal', 'yaml-modal', 'harness-modal', 'how-modal', 'ingest-modal'].forEach(id => {
          const m = document.getElementById(id);
          if (m && (m.classList.contains('open') || m.style.display === 'flex')) {
            closeModal(id);
          }
        });
        const searchInput = document.getElementById('rule-search');
        if (document.activeElement === searchInput) {
          searchInput.blur();
        }
        return;
      }

      // Do not intercept hotkeys if typing inside form fields
      const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      const isInput = tag === 'input' || tag === 'textarea' || tag === 'select' || (document.activeElement && document.activeElement.isContentEditable);
      if (isInput) return;

      if (e.key === '1') {
        e.preventDefault();
        const btn = document.getElementById('tab-btn-rules');
        if (btn) switchTab('tab-rules', btn);
      } else if (e.key === '2') {
        e.preventDefault();
        const btn = document.getElementById('tab-btn-tools');
        if (btn) switchTab('tab-tools', btn);
      } else if (e.key === '3') {
        e.preventDefault();
        const btn = document.getElementById('tab-btn-packs');
        if (btn) switchTab('tab-packs', btn);
      } else if (e.key === '4') {
        e.preventDefault();
        const btn = document.getElementById('tab-btn-incidents');
        if (btn) switchTab('tab-incidents', btn);
      } else if (e.key === '5') {
        e.preventDefault();
        const btn = document.getElementById('tab-btn-inspector');
        if (btn) switchTab('tab-inspector', btn);
      } else if (e.key === '/') {
        e.preventDefault();
        const rulesBtn = document.getElementById('tab-btn-rules');
        if (rulesBtn && !rulesBtn.classList.contains('active')) {
          switchTab('tab-rules', rulesBtn);
        }
        const searchInput = document.getElementById('rule-search');
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      }
    });

    // Initial data hydration
    loadOverview();
    loadRules();
    loadPacks();
    loadHarnesses();
    setInterval(loadOverview, 4000);
  </script>
</body>
</html>
"""


def _get_substrate_dir(root: Path) -> Path:
    sub = root / ".agents" / "substrate"
    if sub.is_dir():
        return sub
    return root / ".agents" / "substrate"


def _get_overview_data(root: Path) -> dict[str, Any]:
    sub_dir = _get_substrate_dir(root)
    rules, _ = discover_rules(sub_dir)
    active_count = sum(1 for r in rules if r.status == "active")
    candidate_count = sum(1 for r in rules if r.status == "candidate")
    archived_count = sum(1 for r in rules if r.status == "archive")

    monitored_paths = [
        ".cursorrules",
        ".windsurfrules",
        ".github/copilot-instructions.md",
        ".git/hooks/pre-commit",
        "CLAUDE.md",
    ]
    connected_count = sum(1 for p in monitored_paths if (root / p).is_file())

    events = read_events(root_dir=root)
    blocked_incidents = [
        e for e in events
        if e.type == "AUTOPSY_RECORD"
        or (e.type == "PEER_CRITIQUE" and "REJECT" in str(e.payload.get("verdict", "")).upper())
    ]
    total_blocked = len(blocked_incidents)

    return {
        "active_rules": active_count,
        "candidate_rules": candidate_count,
        "archived_rules": archived_count,
        "total_rules": len(rules),
        "connected_harnesses": connected_count,
        "total_harnesses": len(monitored_paths),
        "total_blocked_incidents": total_blocked,
        "blocked_incidents": total_blocked,
    }


def _get_harnesses_data(root: Path) -> dict[str, Any]:
    harnesses = [
        {
            "id": "cursor",
            "name": "Cursor IDE",
            "path": ".cursorrules",
            "exists": (root / ".cursorrules").is_file(),
            "tool": "Cursor",
            "description": "Rules injected into Cursor Composer and Chat instructions.",
        },
        {
            "id": "claude",
            "name": "Claude Code",
            "path": "CLAUDE.md",
            "exists": (root / "CLAUDE.md").is_file(),
            "tool": "Claude Code",
            "description": "Repository instructions loaded automatically by Claude Code CLI.",
        },
        {
            "id": "copilot",
            "name": "GitHub Copilot",
            "path": ".github/copilot-instructions.md",
            "exists": (root / ".github" / "copilot-instructions.md").is_file(),
            "tool": "GitHub Copilot",
            "description": "Repository-wide instructions for GitHub Copilot Chat.",
        },
        {
            "id": "windsurf",
            "name": "Windsurf IDE",
            "path": ".windsurfrules",
            "exists": (root / ".windsurfrules").is_file(),
            "tool": "Windsurf",
            "description": "System prompt instructions for Windsurf Cascade agent.",
        },
        {
            "id": "git_hook",
            "name": "Git Pre-Commit Hook",
            "path": ".git/hooks/pre-commit",
            "exists": (root / ".git" / "hooks" / "pre-commit").is_file(),
            "tool": "Git Hook",
            "description": "Deterministic enforcement barrier preventing violation commits.",
        },
    ]
    connected = sum(1 for h in harnesses if h["exists"])
    data: dict[str, Any] = {
        "harnesses": harnesses,
        "connected_count": connected,
        "total_count": len(harnesses),
    }
    for h in harnesses:
        data[h["path"]] = {
            "name": h["name"],
            "path": h["path"],
            "exists": h["exists"],
            "tool": h["tool"],
        }
    return data


def _create_rule(root: Path, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    rule_id = str(payload.get("id", "")).strip()
    if not rule_id:
        return 400, {"error": "Field 'id' must be a non-empty string."}

    statement = str(payload.get("statement", "")).strip()
    if not statement:
        return 400, {"error": "Field 'statement' must be a non-empty string."}

    rationale = str(payload.get("rationale", "")).strip()
    if not rationale:
        rationale = "Guardrail defined via AI Behavior Control Plane."

    raw_paths = payload.get("paths", [])
    if isinstance(raw_paths, str):
        paths = [p.strip() for p in raw_paths.split(",") if p.strip()]
    elif isinstance(raw_paths, list):
        paths = [str(p).strip() for p in raw_paths if str(p).strip()]
    else:
        paths = []
    if not paths:
        paths = ["**/*"]

    raw_langs = payload.get("languages", [])
    if isinstance(raw_langs, str):
        languages = [l.strip() for l in raw_langs.split(",") if l.strip()]
    elif isinstance(raw_langs, list):
        languages = [str(l).strip() for l in raw_langs if str(l).strip()]
    else:
        languages = []

    enforcement = str(payload.get("enforcement", "reject_diff")).strip().lower()
    if enforcement in ("block", "reject", "reject_diff"):
        enforcement = "reject_diff"
    elif enforcement in ("warn", "warning"):
        enforcement = "warn"
    elif enforcement == "audit":
        enforcement = "audit"
    else:
        enforcement = "reject_diff"

    blast_radius = payload.get("max_blast_radius_lines")
    if blast_radius is not None:
        try:
            blast_radius = int(blast_radius)
        except (ValueError, TypeError):
            blast_radius = 30
    else:
        blast_radius = 30

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rule_dict: dict[str, Any] = {
        "id": rule_id,
        "version": 1,
        "status": "active",
        "scope": {
            "paths": paths,
            "languages": languages,
        },
        "invariant": {
            "statement": statement,
            "rationale": rationale,
            "enforcement": enforcement,
            "max_blast_radius_lines": blast_radius,
        },
        "provenance": {
            "incident_id": str(payload.get("incident_id") or f"manual-{int(time.time())}"),
            "git_commit": "HEAD",
            "inscribing_agent": "control-plane-ui",
            "created_at": now_iso,
            "last_verified_at": now_iso,
            "trigger_count": 0,
        },
    }

    is_valid, errors = validate_rule_dict(rule_dict)
    if not is_valid:
        return 400, {"error": "Validation failure", "details": errors}

    sub_dir = _get_substrate_dir(root)
    active_dir = sub_dir / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    target_file = active_dir / f"{rule_id}.yaml"
    with open(target_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(rule_dict, f, sort_keys=False)

    post_event(
        {
            "type": "RULE_CREATED",
            "sender": "control-plane-ui",
            "payload": {
                "rule_id": rule_id,
                "status": "active",
                "statement": statement,
                "file_path": str(target_file),
            },
        },
        root_dir=root,
    )

    return 201, {"success": True, "rule": rule_dict, "path": str(target_file)}


def _toggle_rule(root: Path, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    rule_id = str(payload.get("rule_id") or payload.get("id") or "").strip()
    if not rule_id:
        return 400, {"error": "Field 'rule_id' is required."}

    sub_dir = _get_substrate_dir(root)
    active_dir = sub_dir / "active"
    archive_dir = sub_dir / "archive"
    candidate_dir = sub_dir / "candidate"

    active_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    found_file: Optional[Path] = None
    current_status: str = ""

    # Check active directory
    if active_dir.is_dir():
        for f in list(active_dir.glob("*.yaml")) + list(active_dir.glob("*.yml")):
            if f.stem == rule_id:
                found_file = f
                current_status = "active"
                break
            try:
                d = yaml.safe_load(f.read_text(encoding="utf-8"))
                if isinstance(d, dict) and d.get("id") == rule_id:
                    found_file = f
                    current_status = "active"
                    break
            except Exception:
                pass

    # Check candidate directory
    if not found_file and candidate_dir.is_dir():
        for f in list(candidate_dir.glob("*.yaml")) + list(candidate_dir.glob("*.yml")):
            if f.stem == rule_id:
                found_file = f
                current_status = "candidate"
                break
            try:
                d = yaml.safe_load(f.read_text(encoding="utf-8"))
                if isinstance(d, dict) and d.get("id") == rule_id:
                    found_file = f
                    current_status = "candidate"
                    break
            except Exception:
                pass

    # Check archive directory
    if not found_file and archive_dir.is_dir():
        for f in list(archive_dir.glob("*.yaml")) + list(archive_dir.glob("*.yml")):
            if f.stem == rule_id:
                found_file = f
                current_status = "archive"
                break
            try:
                d = yaml.safe_load(f.read_text(encoding="utf-8"))
                if isinstance(d, dict) and d.get("id") == rule_id:
                    found_file = f
                    current_status = "archive"
                    break
            except Exception:
                pass

    if not found_file or not found_file.is_file():
        return 404, {"error": f"Rule with ID '{rule_id}' not found."}

    try:
        content = found_file.read_text(encoding="utf-8")
        data = yaml.safe_load(content) or {}
    except Exception as exc:
        return 500, {"error": f"Failed to read rule file: {exc}"}

    new_status = "archive" if current_status == "active" else "active"
    target_dir = archive_dir if new_status == "archive" else active_dir
    target_file = target_dir / f"{rule_id}.yaml"

    data["status"] = new_status
    if "provenance" not in data or not isinstance(data["provenance"], dict):
        data["provenance"] = {}
    data["provenance"]["last_verified_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(target_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    if found_file.resolve() != target_file.resolve():
        try:
            found_file.unlink()
        except Exception:
            pass

    post_event(
        {
            "type": "RULE_TOGGLED",
            "sender": "control-plane-ui",
            "payload": {
                "rule_id": rule_id,
                "previous_status": current_status,
                "new_status": new_status,
            },
        },
        root_dir=root,
    )

    return 200, {
        "success": True,
        "rule_id": rule_id,
        "previous_status": current_status,
        "new_status": new_status,
        "file_path": str(target_file),
    }


def _check_file(root: Path, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    file_path = str(payload.get("file_path") or payload.get("path") or "").strip()
    if not file_path:
        return 400, {"error": "Field 'file_path' is required."}

    engine = RuleEngine(root_dir=root)
    matches = engine.match_file(target_path=file_path)
    matched_data = [r.to_dict() for r in matches]

    return 200, {
        "file_path": file_path,
        "matches": matched_data,
        "rules": matched_data,
        "count": len(matched_data),
    }


def _get_incidents(root: Path) -> list[dict[str, Any]]:
    events = read_events(root_dir=root)
    incidents = [
        e.to_dict()
        for e in events
        if e.type in ("AUTOPSY_RECORD", "PEER_CRITIQUE")
    ]
    incidents.reverse()
    return incidents


def _sync_all_harnesses(root: Path) -> dict[str, Any]:
    synced = sync_harnesses(root_dir=root)
    engine = RuleEngine(root_dir=root)
    active_rules = engine.get_rules(status="active")
    rendered = format_rules_for_prompt(active_rules)

    claude_file = root / "CLAUDE.md"
    if claude_file.exists():
        inject_into_file(claude_file, rendered)
        synced["claude"] = claude_file

    return {
        "success": True,
        "synced": [str(p) for p in synced.values()],
        "count": len(synced),
    }


def _check_content_violations(
    root: Path, file_path: str, content: str
) -> tuple[bool, list[dict[str, Any]], int]:
    """Inspect snippet or diff against all applicable active invariant rules."""
    engine = RuleEngine(root_dir=root)
    matching_rules = engine.match_file(target_path=file_path, status="active")
    if not matching_rules:
        return True, [], 0

    from aos.enforcer import check_content_violations
    raw_violations = check_content_violations(file_path, content, matching_rules)
    violations = [v.to_dict() for v in raw_violations]

    has_blocking = any(v.get("enforcement", "reject_diff") == "reject_diff" for v in violations)
    allowed = (len(violations) == 0) or not has_blocking
    return allowed, violations, len(matching_rules)


def _check_content_payload(root: Path, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    file_path = str(payload.get("file_path") or payload.get("path") or "sample.py").strip()
    content = str(payload.get("content") or "")
    allowed, violations, matching_count = _check_content_violations(root, file_path, content)
    return 200, {
        "allowed": allowed,
        "violations": violations,
        "matching_rules_count": matching_count,
        "file_path": file_path,
    }


def _get_rule_yaml(root: Path, rule_id: str) -> tuple[int, dict[str, Any]]:
    sub_dir = _get_substrate_dir(root)
    for folder in ("active", "candidate", "archive"):
        target_dir = sub_dir / folder
        if not target_dir.is_dir():
            continue
        for candidate_file in list(target_dir.glob("*.yaml")) + list(target_dir.glob("*.yml")):
            if candidate_file.stem == rule_id:
                return 200, {
                    "rule_id": rule_id,
                    "status": folder,
                    "path": str(candidate_file),
                    "yaml": candidate_file.read_text(encoding="utf-8"),
                }
            try:
                data = yaml.safe_load(candidate_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and data.get("id") == rule_id:
                    return 200, {
                        "rule_id": rule_id,
                        "status": folder,
                        "path": str(candidate_file),
                        "yaml": candidate_file.read_text(encoding="utf-8"),
                    }
            except Exception:
                pass
    return 404, {"error": f"Rule with ID '{rule_id}' not found."}


def _get_harness_view(root: Path, tool_id: str) -> tuple[int, dict[str, Any]]:
    tool_map = {
        "cursor": (".cursorrules", "Cursor IDE"),
        "claude": ("CLAUDE.md", "Claude Code"),
        "copilot": (".github/copilot-instructions.md", "GitHub Copilot"),
        "windsurf": (".windsurfrules", "Windsurf IDE"),
        "git_hook": (".git/hooks/pre-commit", "Git Pre-Commit Hook"),
    }
    matched = tool_map.get(tool_id)
    if not matched:
        for k, (p, name) in tool_map.items():
            if tool_id in (p, str(Path(p))):
                matched = (p, name)
                tool_id = k
                break

    if not matched:
        return 404, {"error": f"Tool '{tool_id}' not recognized. Available: {list(tool_map.keys())}"}

    rel_path, tool_name = matched
    file_path = root / rel_path
    if file_path.is_file():
        content = file_path.read_text(encoding="utf-8")
        exists = True
    else:
        exists = False
        if tool_id == "git_hook":
            content = "# Pre-commit hook is not installed yet.\n# Click 'Install Git Hook' in dashboard to install.\n"
        else:
            engine = RuleEngine(root_dir=root)
            active_rules = engine.get_rules(status="active")
            rendered = format_rules_for_prompt(active_rules)
            content = f"# Unsynced Preview ({rel_path})\n# Click 'Sync Harnesses' to write to disk:\n\n{rendered}"

    return 200, {
        "id": tool_id,
        "name": tool_name,
        "path": rel_path,
        "exists": exists,
        "content": content,
    }


def _get_packs_data(root: Path) -> list[dict[str, Any]]:
    engine = RuleEngine(root_dir=root)
    active_ids = {r.id for r in engine.get_rules(status="active")}

    pack_meta = {
        "security-core": {
            "title": "Security Core Guardrails",
            "category": "SECURITY",
            "description": "Essential non-negotiable security: blocks hardcoded secrets, SQL injection, SSRF, and unsafe deserialization.",
        },
        "python-core": {
            "title": "Python Core Standards",
            "category": "PYTHON",
            "description": "Standard Python hygiene: bans wildcard imports, enforces structured logging, prevents bare except pass, and detects async blocking I/O.",
        },
        "typescript-core": {
            "title": "TypeScript Core Standards",
            "category": "TYPESCRIPT",
            "description": "Strict TypeScript hygiene: prohibits explicit any, floating promises, React hook dependency issues, and dirty circular imports.",
        },
        "general-hygiene": {
            "title": "General Repository Hygiene",
            "category": "HYGIENE",
            "description": "Universal repo health: manifest and lockfile sync, preventing build artifact commits, and surgical diff blast radius limits.",
        },
        "rust-core": {
            "title": "Rust Core Standards",
            "category": "RUST",
            "description": "Idiomatic Rust invariants: mandatory // SAFETY: comments on unsafe blocks and banning unwrap in library code.",
        },
        "go-core": {
            "title": "Go Core Standards",
            "category": "GOLANG",
            "description": "Idiomatic Go invariants: explicit error handling with %w wrapping and context.Context propagation.",
        },
        "universal-security": {
            "title": "Universal Security Guardrails",
            "category": "SECURITY",
            "description": "Essential non-negotiable security: blocks hardcoded secrets, raw SQL concatenation, and arbitrary eval/exec execution.",
        },
        "security-owasp": {
            "title": "OWASP Top 10 Guardrails",
            "category": "SECURITY",
            "description": "Enterprise protection against SQL injections, credential leaks, and insecure data handling.",
        },
        "web-typescript": {
            "title": "TypeScript Strict Safety",
            "category": "TYPESCRIPT",
            "description": "Type safety invariants banning explicit any casts and floating unhandled async promises.",
        },
        "python-fastapi": {
            "title": "FastAPI & Pydantic Contracts",
            "category": "PYTHON",
            "description": "Typed request/response models with automatic runtime OpenAPI contract validation.",
        },
        "react-modern": {
            "title": "React & Next.js Standards",
            "category": "FRONTEND",
            "description": "Hooks dependency array integrity and client/server component boundary enforcement.",
        },
        "go-standard": {
            "title": "Go Idiomatic Standards",
            "category": "GOLANG",
            "description": "Explicit error wrapping with %w and goroutine termination on context cancellation.",
        },
        "rust-safety": {
            "title": "Rust Unsafe Invariants",
            "category": "RUST",
            "description": "Mandatory SAFETY documentation comments for every unsafe block.",
        },
        "python-clean-architecture": {
            "title": "Python Clean Architecture",
            "category": "ARCHITECTURE",
            "description": "Linting constraints against direct print calls, wildcard imports, and architectural layer drift.",
        },
    }

    packs_list = []
    for name, rules in CURATED_PACKS.items():
        meta = pack_meta.get(name, {"title": name, "category": "GENERAL", "description": "Curated invariant rules."})
        rule_ids = [r["id"] for r in rules]
        installed_count = sum(1 for rid in rule_ids if rid in active_ids)
        packs_list.append({
            "name": name,
            "title": meta["title"],
            "category": meta["category"],
            "description": meta["description"],
            "rule_count": len(rules),
            "rules": rules,
            "installed_count": installed_count,
            "installed": installed_count == len(rules) and len(rules) > 0,
        })

    return packs_list


def _install_pack_payload(root: Path, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    pack_name = str(payload.get("pack_name") or payload.get("name") or "").strip()
    if not pack_name:
        return 400, {"error": "Field 'pack_name' is required."}

    if pack_name not in CURATED_PACKS:
        return 400, {"error": f"Unknown pack '{pack_name}'. Available: {list(CURATED_PACKS.keys())}"}

    try:
        installed = install_pack(pack_name=pack_name, root_dir=root, promote=True)
        post_event(
            {
                "type": "PACK_INSTALLED",
                "sender": "control-plane-ui",
                "payload": {
                    "pack_name": pack_name,
                    "installed_count": len(installed),
                    "installed_paths": [str(p) for p in installed],
                },
            },
            root_dir=root,
        )
        return 200, {
            "success": True,
            "pack_name": pack_name,
            "installed_count": len(installed),
            "installed_paths": [str(p) for p in installed],
            "message": f"Pack '{pack_name}' successfully installed with {len(installed)} active rules.",
        }
    except Exception as exc:
        return 500, {"error": f"Failed to install pack: {exc}"}


class DashboardRequestHandler(BaseHTTPRequestHandler):
    root_dir: Path = Path(".")

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress default console clutter

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
        elif path == "/api/overview":
            data = _get_overview_data(self.root_dir)
            self._send_json(data)
        elif path == "/api/rules":
            sub_dir = _get_substrate_dir(self.root_dir)
            status_filter = query.get("status", [None])[0]
            statuses = {status_filter} if status_filter else None
            rules, _ = discover_rules(sub_dir, statuses=statuses)
            data = [r.to_dict() for r in rules]
            self._send_json(data)
        elif path == "/api/packs":
            packs_data = _get_packs_data(self.root_dir)
            if query.get("format", [""])[0] == "dict":
                self._send_json({"packs": packs_data, "count": len(packs_data)})
            else:
                self._send_json(packs_data)
        elif path == "/api/harnesses":
            data = _get_harnesses_data(self.root_dir)
            if query.get("format", [""])[0] == "list":
                self._send_json(data["harnesses"])
            else:
                self._send_json(data)
        elif path == "/api/harnesses/view":
            tool_id = query.get("id", [""])[0]
            status_code, resp = _get_harness_view(self.root_dir, tool_id)
            self._send_json(resp, status_code=status_code)
        elif path.startswith("/api/rules/") and path.endswith("/yaml"):
            rule_id = path[len("/api/rules/") : -len("/yaml")].strip("/")
            status_code, resp = _get_rule_yaml(self.root_dir, rule_id)
            self._send_json(resp, status_code=status_code)
        elif path == "/api/incidents":
            incidents = _get_incidents(self.root_dir)
            self._send_json(incidents)
        elif path == "/api/events":
            events = read_events(root_dir=self.root_dir)
            data = [e.to_dict() for e in events]
            self._send_json(data)
        elif path == "/api/fleet":
            fleet = list_fleet_rules(fleet_db_path=self.root_dir / ".agents" / "fleet.db")
            self._send_json(fleet)
        elif path == "/api/ingest/scan":
            from aos.ingest import scan_repository_conventions
            report = scan_repository_conventions(self.root_dir)
            self._send_json(report.to_dict())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if path == "/api/rules/create":
            status_code, resp = _create_rule(self.root_dir, payload)
            self._send_json(resp, status_code=status_code)
        elif path == "/api/rules/toggle":
            status_code, resp = _toggle_rule(self.root_dir, payload)
            self._send_json(resp, status_code=status_code)
        elif path == "/api/check-content":
            status_code, resp = _check_content_payload(self.root_dir, payload)
            self._send_json(resp, status_code=status_code)
        elif path == "/api/packs/install":
            status_code, resp = _install_pack_payload(self.root_dir, payload)
            self._send_json(resp, status_code=status_code)
        elif path == "/api/ingest/apply":
            from aos.ingest import ingest_repository
            promote = bool(payload.get("promote", True))
            report = ingest_repository(self.root_dir, auto_promote=promote)
            self._send_json({
                "success": True,
                "report": report.to_dict(),
                "message": f"Successfully ingested and activated {len(report.synthesized_rules)} tailored rule(s).",
            })
        elif path in ("/api/harnesses/sync", "/api/sync"):
            resp = _sync_all_harnesses(self.root_dir)
            self._send_json(resp)
        elif path == "/api/harnesses/hook/install":
            try:
                hook_path = install_git_hook(root_dir=self.root_dir)
                self._send_json({"success": True, "path": str(hook_path)})
            except Exception as exc:
                self._send_json({"success": False, "error": str(exc)}, status_code=500)
        elif path == "/api/check":
            status_code, resp = _check_file(self.root_dir, payload)
            self._send_json(resp, status_code=status_code)
        elif path == "/api/mesh/simulate":
            res = simulate_mesh_cycle(root_dir=self.root_dir)
            self._send_json({"status": res.status, "events_count": len(res.events)})
        elif path == "/api/curate":
            sub_dir = _get_substrate_dir(self.root_dir)
            actions = curate_substrate(substrate_dir=sub_dir)
            self._send_json({"actions_count": len(actions)})
        elif path == "/api/sandbox/simulate-mistake":
            ts = int(time.time())
            rule_id = f"autopsy-sandbox-{ts}"
            candidate = synthesize_candidate_rule(
                rule_id=rule_id,
                statement="Buffer memory must not exceed max allocation limit of 1024 bytes in streaming workers.",
                rationale="Captured memory exhaustion incident during simulation.",
                paths=["src/**"],
                incident_id=f"inc-sandbox-{ts}",
                inscribing_agent="simulation-sentry",
            )
            sub_dir = _get_substrate_dir(self.root_dir)
            saved = inscribe_candidate(candidate, substrate_dir=sub_dir)
            self._send_json({
                "status": "incident_captured_and_autopsied",
                "rule_id": rule_id,
                "path": str(saved),
                "message": "AI attempted forbidden buffer allocation. Invariant Guard intercepted and inscribed candidate rule.",
            })
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data: Any, status_code: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def start_ui_server(port: int = 8484, root_dir: Path | str = ".") -> None:
    """Launch local HTTP visualizer on specified port."""
    root = Path(root_dir)
    DashboardRequestHandler.root_dir = root
    server = HTTPServer(("127.0.0.1", port), DashboardRequestHandler)
    print(f"AOS Control Plane active at http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
