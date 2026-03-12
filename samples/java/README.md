# X API v2 - Java Examples

Working Java code samples for the X (formerly Twitter) API v2.

## Setup

### 1. Install Java 11+

```bash
java --version
```

### 2. Add dependencies

Using Maven, add to your `pom.xml`:

```xml
<dependencies>
    <dependency>
        <groupId>org.apache.httpcomponents</groupId>
        <artifactId>httpclient</artifactId>
        <version>4.5.13</version>
    </dependency>
    <dependency>
        <groupId>com.google.code.gson</groupId>
        <artifactId>gson</artifactId>
        <version>2.9.1</version>
    </dependency>
</dependencies>
```

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

**Note:** Most user action examples require OAuth 2.0 authentication with `CLIENT_ID` and `CLIENT_SECRET`. Read-only examples (search, lookup) only require `BEARER_TOKEN`.

## Examples by Category

### Posts
- `posts/FullArchiveSearchDemo.java` - Full archive search demo
- `posts/FullArchiveTweetCountsDemo.java` - Full archive tweet counts demo
- `posts/QuoteTweetsDemo.java` - Get posts that quote a post
- `posts/RecentSearchDemo.java` - Recent search demo (last 7 days)
- `posts/RecentTweetCountsDemo.java` - Recent tweet counts demo
- `posts/SearchRecent.java` - Recent search (last 7 days)
- `posts/TweetsDemo.java` - Look up posts by ID

### Users
- `users/FollowersLookupDemo.java` - Get user's followers
- `users/FollowingLookupDemo.java` - Get users a user is following
- `users/Lookup.java` - Look up users by username
- `users/UsersDemo.java` - Users lookup demo

### Timelines
- `timelines/reverse-chron-home-timeline-java-sdk.java` - Get home timeline (reverse chronological)
- `timelines/UserMentionsDemo.java` - Get user mentions timeline
- `timelines/UserTweetsDemo.java` - Get user's posts timeline

### Streams
- `streams/FilteredStreamDemo.java` - Filtered stream with rules
- `streams/SampledStream.java` - Sampled stream

### Spaces
- `spaces/SearchSpacesDemo.java` - Search for Spaces
- `spaces/SpacesLookupDemo.java` - Look up Spaces by ID

### Usage
- `usage/UsageTweetsDemo.java` - Get API usage information

## Building and Running

### Compile

```bash
# Compile a single file
javac -cp ".:lib/*" posts/SearchRecent.java

# Or compile all files
find . -name "*.java" -exec javac -cp ".:lib/*" {} \;
```

### Run

```bash
# Run a single example
java -cp ".:lib/*" posts.SearchRecent

# Or with package structure
java -cp ".:lib/*" posts/RecentSearchDemo
```

## More Information

- [X API Documentation](https://developer.x.com/en/docs/twitter-api)
- [X Developer Portal](https://developer.x.com/en/portal/dashboard)
