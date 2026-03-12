# X API v2 - Ruby Examples

Working Ruby code samples for the X (formerly Twitter) API v2.

## Setup

### 1. Install Ruby 2.7+

```bash
ruby --version
```

### 2. Install dependencies

```bash
bundle install
```

Or manually:
```bash
gem install typhoeus
gem install oauth  # For OAuth 1.0a examples
```

The `Gemfile` includes:
- `typhoeus` (~> 1.4) - HTTP client library
- `oauth` (~> 1.1) - OAuth 1.0a library

### 3. Set environment variables

**For read-only operations (search, lookup):**
```bash
export BEARER_TOKEN='your_bearer_token'
```

**For user actions (post, like, repost, bookmark, etc.):**
```bash
export CLIENT_ID='your_client_id'
export CLIENT_SECRET='your_client_secret'
```

**For OAuth 1.0a (legacy endpoints):**
```bash
export CONSUMER_KEY='your_consumer_key'
export CONSUMER_SECRET='your_consumer_secret'
```

**Note:** Most user action examples require OAuth 2.0 authentication with `CLIENT_ID` and `CLIENT_SECRET`. Read-only examples (search, lookup) only require `BEARER_TOKEN`.

## Examples by Category

### Posts
- `posts/create_tweet.rb` - Create a new post
- `posts/delete_tweet.rb` - Delete a post
- `posts/full_archive_tweet_counts.rb` - Full archive tweet counts
- `posts/full-archive-search.rb` - Full archive search
- `posts/get_tweets_with_bearer_token.rb` - Look up posts by ID (bearer token)
- `posts/get_tweets_with_user_context.rb` - Look up posts by ID (user context)
- `posts/like_a_tweet.rb` - Like a post
- `posts/liked_tweets.rb` - Get posts liked by a user
- `posts/liking_users.rb` - Get users who liked a post
- `posts/lookup.rb` - Look up posts by ID
- `posts/quote_tweets.rb` - Get posts that quote a post
- `posts/recent_search.rb` - Recent search (last 7 days)
- `posts/recent_tweet_counts.rb` - Recent tweet counts
- `posts/retweet_a_tweet.rb` - Repost a post
- `posts/retweeted_by.rb` - Get users who reposted a post
- `posts/search_recent.rb` - Recent search (alternative)
- `posts/undo_a_retweet.rb` - Undo a repost
- `posts/unlike_a_tweet.rb` - Unlike a post

### Users
- `users/block_a_user.rb` - Block a user
- `users/followers-lookup.rb` - Get user's followers (lookup)
- `users/followers.rb` - Get user's followers
- `users/following-lookup.rb` - Get users a user is following
- `users/get_users_me_with_user_context.rb` - Get authenticated user (me)
- `users/get_users_with_bearer_token.rb` - Look up users by username (bearer token)
- `users/get_users_with_user_context.rb` - Look up users by username (user context)
- `users/lookup_blocks.rb` - Get users blocked by a user
- `users/lookup_mutes.rb` - Get users muted by a user
- `users/lookup.rb` - Look up users by username
- `users/mute_a_user.rb` - Mute a user
- `users/unblock_a_user.rb` - Unblock a user
- `users/unmute_a_user.rb` - Unmute a user

### Timelines
- `timelines/reverse-chron-home-timeline.rb` - Get home timeline (reverse chronological)
- `timelines/user_posts.rb` - Get user's posts timeline
- `timelines/user-mentions.rb` - Get user mentions timeline
- `timelines/user-tweets.rb` - Get user's tweets timeline

### Streams
- `streams/filtered_stream.rb` - Filtered stream with rules
- `streams/sampled_stream.rb` - Sampled stream

### Lists
- `lists/add_member.rb` - Add member to a list
- `lists/create_a_list.rb` - Create a new list
- `lists/delete_a_list.rb` - Delete a list
- `lists/follow_list.rb` - Follow a list
- `lists/list-followers-lookup.rb` - Get list followers
- `lists/list-lookup-by-id.rb` - Get list by ID
- `lists/list-member-lookup.rb` - Get list members
- `lists/List-Tweets.rb` - Get posts from a list
- `lists/lookup.rb` - Look up a list
- `lists/pin_list.rb` - Pin a list
- `lists/Pinned-List.rb` - Get pinned lists
- `lists/remove_member.rb` - Remove member from a list
- `lists/unfollow_list.rb` - Unfollow a list
- `lists/unpin_list.rb` - Unpin a list
- `lists/update_a_list.rb` - Update a list
- `lists/user-list-followed.rb` - Get lists followed by a user
- `lists/user-list-memberships.rb` - Get list memberships
- `lists/user-owned-list-lookup.rb` - Get lists owned by a user

### Bookmarks
- `bookmarks/bookmarks_lookup.rb` - Get user's bookmarks

### Spaces
- `spaces/search_spaces.rb` - Search for Spaces
- `spaces/spaces_lookup.rb` - Look up Spaces by ID

## Running Examples

```bash
# Make sure environment variables are set
ruby posts/search_recent.rb
```

## More Information

- [X API Documentation](https://developer.x.com/en/docs/twitter-api)
- [X Developer Portal](https://developer.x.com/en/portal/dashboard)
