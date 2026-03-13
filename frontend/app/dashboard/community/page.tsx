"use client";

import { useState, useEffect } from "react";
import {
  Users,
  MessageSquare,
  ThumbsUp,
  Send,
  Loader2,
  Plus,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";

interface Post {
  id: string;
  user_name: string;
  title: string;
  body: string;
  category: string;
  crop: string;
  upvotes: number;
  replies_count: number;
  is_answered: boolean;
  created_at: string;
}

interface Reply {
  id: string;
  user_name: string;
  body: string;
  is_expert: boolean;
  upvotes: number;
  created_at: string;
}

const CATEGORIES = ["general", "disease", "soil", "weather", "market", "equipment"];

export default function CommunityPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [replies, setReplies] = useState<Reply[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [category, setCategory] = useState("");

  // New post form
  const [newTitle, setNewTitle] = useState("");
  const [newBody, setNewBody] = useState("");
  const [newCategory, setNewCategory] = useState("general");
  const [newCrop, setNewCrop] = useState("");
  const [posting, setPosting] = useState(false);

  useEffect(() => {
    loadPosts();
  }, [category]);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const res = await api.community.posts(category || undefined);
      setPosts(res.posts as Post[]);
    } catch {
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };

  const openPost = async (post: Post) => {
    setSelectedPost(post);
    try {
      const res = await api.community.getPost(post.id);
      setReplies(res.replies as Reply[]);
    } catch {
      setReplies([]);
    }
  };

  const submitPost = async () => {
    if (!newTitle.trim()) return;
    setPosting(true);
    try {
      const form = new FormData();
      form.append("title", newTitle);
      form.append("body", newBody);
      form.append("category", newCategory);
      if (newCrop) form.append("crop", newCrop);
      await api.community.createPost(form);
      setShowNew(false);
      setNewTitle("");
      setNewBody("");
      loadPosts();
    } catch {
      // ignore
    } finally {
      setPosting(false);
    }
  };

  const submitReply = async () => {
    if (!selectedPost || !replyText.trim()) return;
    try {
      await api.community.reply(selectedPost.id, replyText);
      setReplyText("");
      openPost(selectedPost);
    } catch {
      // ignore
    }
  };

  const upvote = async (postId: string) => {
    await api.community.upvote(postId);
    loadPosts();
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / 3600000);
    if (hours < 1) return "Just now";
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div className="animate-fade-in max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Users className="w-8 h-8 text-teal-500" />
            Community
          </h1>
          <p className="text-gray-500 mt-1">
            Ask questions, share knowledge, and connect with experts
          </p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="px-4 py-2 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 transition flex items-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" /> New Post
        </button>
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategory("")}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
            !category ? "bg-teal-100 text-teal-700" : "bg-gray-100 text-gray-500"
          }`}
        >
          All
        </button>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium capitalize transition ${
              category === c
                ? "bg-teal-100 text-teal-700"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {/* New Post Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6">
            <h2 className="text-xl font-bold mb-4">New Post</h2>
            <input
              placeholder="Title / Question"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg mb-3 text-sm focus:ring-2 focus:ring-teal-500"
            />
            <textarea
              placeholder="Describe your question or share details..."
              value={newBody}
              onChange={(e) => setNewBody(e.target.value)}
              rows={4}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg mb-3 text-sm focus:ring-2 focus:ring-teal-500 resize-none"
            />
            <div className="flex gap-3 mb-4">
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <input
                placeholder="Crop (optional)"
                value={newCrop}
                onChange={(e) => setNewCrop(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
              />
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowNew(false)}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={submitPost}
                disabled={posting || !newTitle.trim()}
                className="px-5 py-2 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50 text-sm"
              >
                {posting ? "Posting..." : "Post"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Post Detail */}
      {selectedPost && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] overflow-y-auto p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">{selectedPost.title}</h2>
                <p className="text-sm text-gray-500">
                  {selectedPost.user_name} · {timeAgo(selectedPost.created_at)} ·{" "}
                  <span className="capitalize">{selectedPost.category}</span>
                </p>
              </div>
              <button
                onClick={() => setSelectedPost(null)}
                className="text-gray-400 hover:text-gray-600 text-xl"
              >
                ×
              </button>
            </div>

            {selectedPost.body && (
              <p className="text-gray-700 mb-6">{selectedPost.body}</p>
            )}

            {/* Replies */}
            <div className="border-t border-gray-100 pt-4 mb-4">
              <h3 className="font-semibold text-gray-700 mb-3">
                {replies.length} Replies
              </h3>
              <div className="space-y-3">
                {replies.map((r) => (
                  <div
                    key={r.id}
                    className={`p-4 rounded-lg ${
                      r.is_expert ? "bg-green-50 border border-green-200" : "bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">
                        {r.user_name}
                      </span>
                      {r.is_expert && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                          Expert
                        </span>
                      )}
                      <span className="text-xs text-gray-400">
                        {timeAgo(r.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{r.body}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Reply Input */}
            <div className="flex gap-2">
              <input
                placeholder="Write a reply..."
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submitReply()}
                className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-teal-500"
              />
              <button
                onClick={submitReply}
                disabled={!replyText.trim()}
                className="px-4 py-2.5 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Posts List */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="w-8 h-8 animate-spin text-teal-500" />
        </div>
      ) : posts.length > 0 ? (
        <div className="space-y-3">
          {posts.map((post) => (
            <div
              key={post.id}
              className="bg-white rounded-xl border border-gray-100 p-5 card-hover cursor-pointer"
              onClick={() => openPost(post)}
            >
              <div className="flex items-start gap-4">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    upvote(post.id);
                  }}
                  className="flex flex-col items-center gap-0.5 text-gray-400 hover:text-teal-600 transition pt-1"
                >
                  <ThumbsUp className="w-4 h-4" />
                  <span className="text-xs font-medium">{post.upvotes}</span>
                </button>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900 truncate">
                      {post.title}
                    </h3>
                    {post.is_answered && (
                      <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
                    )}
                  </div>
                  {post.body && (
                    <p className="text-sm text-gray-500 line-clamp-2">
                      {post.body}
                    </p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span>{post.user_name}</span>
                    <span>{timeAgo(post.created_at)}</span>
                    <span className="capitalize">{post.category}</span>
                    {post.crop && (
                      <span className="text-agri-600 capitalize">
                        {post.crop}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <MessageSquare className="w-3 h-3" /> {post.replies_count}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 text-gray-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-3" />
          <p className="text-lg">No posts yet</p>
          <p className="text-sm mt-1">Be the first to start a discussion!</p>
        </div>
      )}
    </div>
  );
}
