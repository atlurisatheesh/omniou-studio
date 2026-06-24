"""
CLONEAI ULTRA — Script-to-Video Generator
============================================
Takes a narration script and generates a full-length talking-head video
using the identity-locked pipeline.

Usage:
    python generate_from_script.py \
        --photo "uploads/photos/your_photo.jpg" \
        --voice "uploads/voices/your_voice.wav" \
        --script "VIDEO_NARRATION_SCRIPTS.md" \
        --video-index 1 \
        --emotion professional

    Or generate ALL videos:
    python generate_from_script.py \
        --photo "uploads/photos/your_photo.jpg" \
        --voice "uploads/voices/your_voice.wav" \
        --script "VIDEO_NARRATION_SCRIPTS.md" \
        --all
"""

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.app.services.identity_anchor import IdentityAnchorService
from backend.app.services.director_agent import DirectorAgent
from backend.app.config import settings


def parse_scripts_from_markdown(md_path: str) -> list:
    """
    Parse VIDEO_NARRATION_SCRIPTS.md and extract each video's script.
    
    Returns list of dicts:
      [{"title": "Product Overview", "duration": "2 min", "script": "...", "index": 1}, ...]
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Pattern: ## VIDEO N: Title (duration)
    video_pattern = re.compile(
        r"## VIDEO (\d+):\s*(.+?)\s*\((.+?)\)\s*\n"
        r".*?\n### Script:\s*\n```\s*\n(.*?)```",
        re.DOTALL,
    )
    
    videos = []
    for match in video_pattern.finditer(content):
        index = int(match.group(1))
        title = match.group(2).strip()
        duration = match.group(3).strip()
        script = match.group(4).strip()
        
        word_count = len(script.split())
        estimated_seconds = word_count / 2.5
        estimated_minutes = estimated_seconds / 60
        
        videos.append({
            "index": index,
            "title": title,
            "duration_label": duration,
            "script": script,
            "word_count": word_count,
            "estimated_seconds": round(estimated_seconds, 1),
            "estimated_minutes": round(estimated_minutes, 1),
        })
    
    return videos


async def generate_video(
    photo_path: str,
    voice_path: str,
    script_text: str,
    video_title: str,
    video_index: int,
    emotion: str = "professional",
    output_dir: str = "outputs/narration_videos",
):
    """Generate a single video from a narration script."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"🎬 Generating: VIDEO {video_index} — {video_title}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Step 1: Create identity anchor
    print("\n🔒 Step 1: Creating identity anchor from your photo + voice...")
    anchor_service = IdentityAnchorService()
    anchor = await anchor_service.create_anchor(
        photo_path=photo_path,
        voice_path=voice_path,
    )
    
    print(f"   ✅ Anchor created: {anchor.anchor_id}")
    print(f"   📸 Face embedding: {'✅' if anchor.face_embedding is not None else '❌'}")
    print(f"   🎙️ Voice embedding: {'✅' if anchor.has_voice() else '❌'}")
    
    # Step 2: Analyze script and split into scenes
    print("\n📝 Step 2: Analyzing script and splitting into scenes...")
    director = DirectorAgent(
        identity_anchor=anchor,
        device=settings.DEVICE,
        model_cache_dir=settings.MODEL_CACHE_DIR,
    )
    
    word_count = len(script_text.split())
    target_minutes = max(1, word_count / 150)  # ~150 words per minute
    
    scenes = await director.analyze_script(
        script_text=script_text,
        target_duration_minutes=target_minutes,
        default_emotion=emotion,
    )
    
    print(f"   ✅ Split into {len(scenes)} scenes:")
    for scene in scenes:
        print(f"      Scene {scene.scene_index + 1}: {scene.word_count} words, ~{scene.duration_seconds:.0f}s, emotion={scene.emotion}")
    
    total_duration = sum(s.duration_seconds for s in scenes)
    print(f"   ⏱️ Total estimated duration: {total_duration/60:.1f} minutes")
    
    # Step 3: Generate project
    project_id = f"narration_video_{video_index:02d}"
    print(f"\n🚀 Step 3: Generating {len(scenes)} scenes with identity lock...")
    print(f"   Project ID: {project_id}")
    print(f"   Identity threshold: {settings.IDENTITY_SIMILARITY_THRESHOLD}")
    print(f"   Max retries per scene: {settings.IDENTITY_MAX_RETRIES}")
    
    result = await director.generate_project(project_id, scenes)
    
    elapsed = time.time() - start_time
    
    # Step 4: Report
    print(f"\n{'='*60}")
    print(f"📊 RESULT — VIDEO {video_index}: {video_title}")
    print(f"{'='*60}")
    print(f"   Status: {result.status}")
    print(f"   Scenes completed: {result.completed_scenes}/{result.total_scenes}")
    print(f"   Failed scenes: {result.failed_scenes}")
    print(f"   Overall identity score: {result.overall_identity_score:.2f}" if result.overall_identity_score else "   Overall identity score: N/A")
    print(f"   Overall color score: {result.overall_color_score:.2f}" if result.overall_color_score else "   Overall color score: N/A")
    print(f"   Output video: {result.final_video_path}")
    print(f"   Processing time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    
    if result.scene_results:
        print(f"\n   Per-scene breakdown:")
        for sr in result.scene_results:
            status_icon = "✅" if sr.status == "completed" else "🔧" if sr.status == "corrected" else "❌"
            print(f"      Scene {sr.scene_index + 1}: {status_icon} identity={sr.identity_score:.2f} color={sr.color_score:.2f} drift={sr.drift_frame_count}")
    
    return result


async def main():
    parser = argparse.ArgumentParser(description="Generate narration videos from scripts")
    parser.add_argument("--photo", required=True, help="Path to your face photo")
    parser.add_argument("--voice", required=True, help="Path to your voice sample (min 6s)")
    parser.add_argument("--script", required=True, help="Path to VIDEO_NARRATION_SCRIPTS.md")
    parser.add_argument("--video-index", type=int, help="Generate a specific video (1-12)")
    parser.add_argument("--all", action="store_true", help="Generate ALL videos")
    parser.add_argument("--emotion", default="professional", help="Default emotion")
    parser.add_argument("--output-dir", default="outputs/narration_videos", help="Output directory")
    parser.add_argument("--list", action="store_true", help="List all scripts without generating")
    
    args = parser.parse_args()
    
    # Parse scripts
    scripts = parse_scripts_from_markdown(args.script)
    
    if not scripts:
        print("❌ No scripts found in the file!")
        return
    
    # List mode
    if args.list:
        print(f"\n📋 Found {len(scripts)} video scripts:\n")
        total_words = 0
        total_seconds = 0
        for s in scripts:
            print(f"  VIDEO {s['index']:2d}: {s['title']}")
            print(f"           {s['word_count']} words • ~{s['estimated_minutes']} min • {s['duration_label']}")
            total_words += s['word_count']
            total_seconds += s['estimated_seconds']
        print(f"\n  TOTAL: {total_words} words • ~{total_seconds/60:.1f} minutes")
        return
    
    # Validate inputs
    if not Path(args.photo).exists():
        print(f"❌ Photo not found: {args.photo}")
        return
    
    if not Path(args.voice).exists():
        print(f"❌ Voice sample not found: {args.voice}")
        return
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║     CLONEAI PRO — Script-to-Video Generator                 ║
║     Identity-Locked Long-Form Video Production              ║
╠══════════════════════════════════════════════════════════════╣
║  Photo:     {args.photo:<46s}  ║
║  Voice:     {args.voice:<46s}  ║
║  Scripts:   {len(scripts)} videos found                                   ║
║  Emotion:   {args.emotion:<46s}  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    if args.video_index:
        # Generate specific video
        target = [s for s in scripts if s["index"] == args.video_index]
        if not target:
            print(f"❌ Video {args.video_index} not found! Available: {[s['index'] for s in scripts]}")
            return
        
        script = target[0]
        result = await generate_video(
            photo_path=args.photo,
            voice_path=args.voice,
            script_text=script["script"],
            video_title=script["title"],
            video_index=script["index"],
            emotion=args.emotion,
            output_dir=args.output_dir,
        )
        results.append((script, result))
    
    elif args.all:
        # Generate ALL videos
        print(f"\n🎬 Generating ALL {len(scripts)} videos...\n")
        
        for script in scripts:
            result = await generate_video(
                photo_path=args.photo,
                voice_path=args.voice,
                script_text=script["script"],
                video_title=script["title"],
                video_index=script["index"],
                emotion=args.emotion,
                output_dir=args.output_dir,
            )
            results.append((script, result))
    
    else:
        print("❌ Specify --video-index N or --all")
        return
    
    # Final summary
    if results:
        print(f"\n{'='*60}")
        print(f"📊 FINAL SUMMARY — {len(results)} Videos Generated")
        print(f"{'='*60}")
        
        total_time = 0
        for script, result in results:
            status = "✅" if result.status == "completed" else "⚠️" if result.status == "partial" else "❌"
            identity = f"{result.overall_identity_score:.0%}" if result.overall_identity_score else "N/A"
            print(f"  {status} VIDEO {script['index']:2d}: {script['title']:<40s} Identity: {identity}")
            total_time += result.processing_time_seconds or 0
        
        print(f"\n  Total processing time: {total_time/60:.1f} minutes")
        print(f"  Output directory: {args.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
