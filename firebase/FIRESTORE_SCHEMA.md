# Firestore Database Schema

This document describes the Firestore collections used by the Papito Mamito AI autonomous agent.

---

## Collections Overview

```
├── content_queue          # Posts pending approval/publishing
├── published_content      # Archive of posted content
├── scheduled_posts        # Content calendar
├── fan_interactions       # Comments, mentions, DMs
├── engagement_actions     # Likes, follows, replies to execute
├── analytics_snapshots    # Performance metrics
├── fans                   # Fan profiles
├── platform_connections   # OAuth tokens for social platforms
└── agent_logs             # Autonomous agent activity logs
```

---

## Collection Schemas

### content_queue
Posts waiting to be approved or published.

```javascript
{
  id: string,                    // Auto-generated
  content_type: string,          // "blog", "track_teaser", "fan_shoutout", "gratitude"
  platform: string,              // "instagram", "x", "tiktok", "all"
  
  // Content data
  title: string,
  body: string,
  media_urls: string[],          // Images/videos to post
  hashtags: string[],
  
  // Platform-specific formatted content
  formatted: {
    instagram: {
      caption: string,
      carousel_slides: object[],
    },
    x: {
      tweets: string[],          // Thread of tweets
      media_ids: string[],
    }
  },
  
  // Approval workflow
  status: string,                // "pending_review", "approved", "rejected", "published", "failed"
  auto_approve: boolean,         // True for 80% auto-approved content
  requires_review: boolean,
  reviewed_by: string | null,
  reviewed_at: timestamp | null,
  rejection_reason: string | null,
  
  // Scheduling
  scheduled_at: timestamp,       // When to publish
  
  // Metadata
  created_at: timestamp,
  updated_at: timestamp,
  source_blog_id: string | null, // Reference to source blog if adapted
  source_track_id: string | null,
}
```

---

### published_content
Archive of successfully published content.

```javascript
{
  id: string,
  queue_id: string,              // Reference to original content_queue item
  
  platform: string,              // "instagram", "x", "tiktok"
  platform_post_id: string,      // ID from the platform (e.g., tweet ID)
  platform_url: string,          // Direct URL to the post
  
  content_type: string,
  title: string,
  body: string,
  
  // Performance metrics
  metrics: {
    likes: number,
    comments: number,
    shares: number,
    impressions: number,
    reach: number,
    engagement_rate: number,
  },
  metrics_updated_at: timestamp,
  
  published_at: timestamp,
  created_at: timestamp,
}
```

---

### scheduled_posts
Future content calendar entries.

```javascript
{
  id: string,
  
  // Schedule details
  scheduled_at: timestamp,
  timezone: string,              // "Africa/Lagos" (WAT)
  recurrence: string | null,     // "daily", "weekly", null for one-time
  
  // Content type
  post_type: string,             // "morning_blessing", "afternoon_engagement", "evening_spotlight", "custom"
  
  // Content generation params (if auto-generating)
  generation_params: {
    mood: string,
    theme: string,
    focus_track: string | null,
  },
  
  // Or direct content
  content_id: string | null,     // Reference to content_queue
  
  status: string,                // "scheduled", "generating", "ready", "published", "failed"
  last_run_at: timestamp | null,
  
  created_at: timestamp,
  updated_at: timestamp,
}
```

---

### fan_interactions
Comments, mentions, and DMs that need response.

```javascript
{
  id: string,
  
  platform: string,              // "instagram", "x"
  platform_interaction_id: string,
  interaction_type: string,      // "comment", "mention", "dm", "reply"
  
  // Source
  post_id: string | null,        // Platform post ID if it's a comment
  fan_username: string,
  fan_display_name: string,
  fan_profile_url: string,
  
  // Content
  message: string,               // The fan's message
  media_urls: string[],          // Any attached media
  
  // Response handling
  status: string,                // "pending", "responding", "responded", "ignored", "flagged"
  response: string | null,
  response_id: string | null,    // Platform ID of our response
  responded_at: timestamp | null,
  
  // AI analysis
  sentiment: string,             // "positive", "neutral", "negative"
  requires_human: boolean,       // True if AI flagged for human review
  
  received_at: timestamp,
  created_at: timestamp,
  updated_at: timestamp,
}
```

---

### engagement_actions
Proactive engagement actions (likes, follows, etc.).

```javascript
{
  id: string,
  
  platform: string,              // "instagram", "x"
  action_type: string,           // "like", "follow", "retweet", "comment"
  
  // Target
  target_user: string,           // Username to engage with
  target_post_id: string | null, // Post ID if liking/commenting
  
  // For comments
  message: string | null,
  
  // Execution
  status: string,                // "pending", "executing", "completed", "failed"
  priority: number,              // 1-10, higher = more important
  error_message: string | null,
  
  executed_at: timestamp | null,
  created_at: timestamp,
}
```

---

### analytics_snapshots
Performance metrics collected periodically.

```javascript
{
  id: string,
  
  platform: string,              // "instagram", "x", "all"
  snapshot_type: string,         // "daily", "weekly", "monthly"
  
  // Account metrics
  account_metrics: {
    followers: number,
    following: number,
    posts_count: number,
    followers_gained: number,
    followers_lost: number,
  },
  
  // Content performance
  content_metrics: {
    total_posts: number,
    total_likes: number,
    total_comments: number,
    total_shares: number,
    avg_engagement_rate: number,
    top_post_id: string,
  },
  
  // Engagement metrics
  engagement_metrics: {
    comments_received: number,
    comments_responded: number,
    mentions: number,
    dm_count: number,
  },
  
  period_start: timestamp,
  period_end: timestamp,
  collected_at: timestamp,
}
```

---

### fans
Fan profiles (migrated from JSON).

```javascript
{
  id: string,
  
  name: string,
  location: string | null,
  support_level: string,         // "casual", "core", "ambassador"
  favorite_tracks: string[],
  notes: string | null,
  
  // Social handles
  instagram_handle: string | null,
  x_handle: string | null,
  
  // Engagement history
  total_interactions: number,
  last_interaction_at: timestamp | null,
  
  join_date: timestamp,
  created_at: timestamp,
  updated_at: timestamp,
}
```

---

### platform_connections
OAuth tokens and connection status for social platforms.

```javascript
{
  id: string,                    // Platform name: "instagram", "x", "buffer"
  
  status: string,                // "connected", "disconnected", "expired", "error"
  
  // OAuth credentials (encrypted)
  access_token: string,
  refresh_token: string | null,
  token_expires_at: timestamp | null,
  
  // Platform-specific IDs
  platform_user_id: string,
  platform_username: string,
  
  // Rate limiting
  rate_limit_remaining: number | null,
  rate_limit_reset_at: timestamp | null,
  
  connected_at: timestamp,
  last_used_at: timestamp | null,
  updated_at: timestamp,
}
```

---

### agent_logs
Activity logs from the autonomous agent.

```javascript
{
  id: string,
  
  agent_session_id: string,      // Unique ID for agent run session
  
  action: string,                // "post_published", "comment_responded", "error", etc.
  level: string,                 // "info", "warning", "error"
  
  message: string,
  details: object,               // Additional context
  
  // References
  content_id: string | null,
  interaction_id: string | null,
  platform: string | null,
  
  created_at: timestamp,
}
```
