import logging
import requests
from typing import Optional, Dict, Any
from os import getenv
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reddit's API base URL
REDDIT_API_BASE = "https://www.reddit.com"
USER_AGENT = getenv("REDDIT_USER_AGENT", "RRR-Research/1.0")

# Session for connection pooling
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

# Initialize MCP
mcp = FastMCP("Reddit MCP")

def _get_reddit_json(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Fetch JSON from Reddit API using direct HTTP requests."""
    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        raise

@mcp.tool()
def search_posts(
    query: str,
    subreddit: Optional[str] = None,
    sort: str = "relevance",
    time_filter: str = "all",
    limit: int = 25,
) -> Dict[str, Any]:
    """Search Reddit posts by keyword.

    Args:
        query: Search term (e.g., "solar contract problems")
        subreddit: Subreddit to search in (optional, omit 'r/' prefix)
        sort: Sort order - 'relevance', 'hot', 'top', 'new', 'comments'
        time_filter: Time range - 'hour', 'day', 'week', 'month', 'year', 'all'
        limit: Number of results to return (1-100)
    """
    if subreddit:
        url = f"{REDDIT_API_BASE}/r/{subreddit}/search.json"
    else:
        url = f"{REDDIT_API_BASE}/search.json"

    params = {
        "q": query,
        "sort": sort,
        "t": time_filter,
        "limit": min(limit, 100),
    }

    data = _get_reddit_json(url, params)

    posts = []
    if "data" in data and "children" in data["data"]:
        for item in data["data"]["children"]:
            if item["kind"] == "t3":  # t3 = post/submission
                post = item["data"]
                posts.append({
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "author": post.get("author", "[deleted]"),
                    "subreddit": post.get("subreddit"),
                    "score": post.get("score"),
                    "upvote_ratio": post.get("upvote_ratio"),
                    "num_comments": post.get("num_comments"),
                    "created_utc": post.get("created_utc"),
                    "url": post.get("url"),
                    "permalink": post.get("permalink"),
                    "is_self": post.get("is_self"),
                    "selftext": post.get("selftext", ""),
                })

    return {
        "query": query,
        "subreddit": subreddit,
        "posts": posts,
        "result_count": len(posts),
    }


@mcp.tool()
def get_top_posts(
    subreddit: str,
    time_filter: str = "week",
    limit: int = 20,
) -> Dict[str, Any]:
    """Get trending posts from a subreddit.

    Args:
        subreddit: Subreddit name (omit 'r/' prefix)
        time_filter: Time range - 'hour', 'day', 'week', 'month', 'year', 'all'
        limit: Number of posts to return (1-100)
    """
    url = f"{REDDIT_API_BASE}/r/{subreddit}/top.json"
    params = {
        "t": time_filter,
        "limit": min(limit, 100),
    }

    data = _get_reddit_json(url, params)

    posts = []
    if "data" in data and "children" in data["data"]:
        for item in data["data"]["children"]:
            if item["kind"] == "t3":
                post = item["data"]
                posts.append({
                    "id": post.get("id"),
                    "title": post.get("title"),
                    "author": post.get("author", "[deleted]"),
                    "subreddit": post.get("subreddit"),
                    "score": post.get("score"),
                    "upvote_ratio": post.get("upvote_ratio"),
                    "num_comments": post.get("num_comments"),
                    "created_utc": post.get("created_utc"),
                    "url": post.get("url"),
                    "permalink": post.get("permalink"),
                    "is_self": post.get("is_self"),
                    "selftext": post.get("selftext", ""),
                })

    return {
        "subreddit": subreddit,
        "time_filter": time_filter,
        "posts": posts,
        "result_count": len(posts),
    }


@mcp.tool()
def get_subreddit_stats(subreddit: str) -> Dict[str, Any]:
    """Get information about a subreddit.

    Args:
        subreddit: Subreddit name (omit 'r/' prefix)
    """
    url = f"{REDDIT_API_BASE}/r/{subreddit}/about.json"
    data = _get_reddit_json(url)

    if "data" in data:
        info = data["data"]
        return {
            "subreddit": subreddit,
            "title": info.get("title"),
            "description": info.get("public_description"),
            "subscribers": info.get("subscribers"),
            "active_users": info.get("active_user_count"),
            "created_utc": info.get("created_utc"),
            "over_18": info.get("over18"),
        }

    return {"error": f"Could not fetch stats for r/{subreddit}"}


@mcp.tool()
def get_submission_by_id(
    submission_id: str,
    include_comments: bool = False,
) -> Dict[str, Any]:
    """Get a specific Reddit post by ID.

    Args:
        submission_id: Reddit post ID (can include 't3_' prefix)
        include_comments: Whether to include comment thread
    """
    # Clean up ID
    if submission_id.startswith("t3_"):
        submission_id = submission_id[3:]

    url = f"{REDDIT_API_BASE}/r/all/comments/{submission_id}.json"
    data = _get_reddit_json(url)

    if isinstance(data, list) and len(data) > 0:
        post_data = data[0]
        if "data" in post_data and "children" in post_data["data"]:
            post = post_data["data"]["children"][0]["data"]

            result = {
                "id": post.get("id"),
                "title": post.get("title"),
                "author": post.get("author", "[deleted]"),
                "subreddit": post.get("subreddit"),
                "score": post.get("score"),
                "upvote_ratio": post.get("upvote_ratio"),
                "num_comments": post.get("num_comments"),
                "created_utc": post.get("created_utc"),
                "url": post.get("url"),
                "permalink": post.get("permalink"),
                "is_self": post.get("is_self"),
                "selftext": post.get("selftext", ""),
            }

            if include_comments and len(data) > 1:
                comments_data = data[1]
                comments = []
                if "data" in comments_data and "children" in comments_data["data"]:
                    for comment_item in comments_data["data"]["children"][:20]:  # Limit to first 20
                        if comment_item["kind"] == "t1":  # t1 = comment
                            comment = comment_item["data"]
                            comments.append({
                                "author": comment.get("author", "[deleted]"),
                                "body": comment.get("body"),
                                "score": comment.get("score"),
                                "created_utc": comment.get("created_utc"),
                            })
                result["comments"] = comments

            return result

    return {"error": f"Could not fetch post {submission_id}"}


if __name__ == "__main__":
    logger.info("Starting Reddit MCP server (HTTP-based, no authentication required)")
    mcp.run()
