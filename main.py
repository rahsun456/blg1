import streamlit as st
import json
from utils.feed_parser import FeedParser
import os
from utils.content_generator import ContentGenerator
from utils.wordpress_api import WordPressAPI
from utils.seo_optimizer import SEOOptimizer

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'feed_parser' not in st.session_state:
    st.session_state.feed_parser = FeedParser()
if 'content_generator' not in st.session_state:
    st.session_state.content_generator = ContentGenerator()
if 'seo_optimizer' not in st.session_state:
    st.session_state.seo_optimizer = SEOOptimizer()
if 'wordpress_api' not in st.session_state:
    st.session_state.wordpress_api = None
if 'feed_cache' not in st.session_state:
    st.session_state.feed_cache = {}
if 'content_cache' not in st.session_state:
    st.session_state.content_cache = {}
if 'site_config' not in st.session_state:
    st.session_state.site_config = {}

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Site Management", "Bulk Article Generator"])
st.session_state.page = page.lower()

if st.session_state.page == "home":
    # App title and description
    st.title("AI Content Generator")
    st.markdown("""
    Generate SEO-optimized blog posts from RSS feeds and publish to WordPress.
    """)

    # WordPress Configuration Section
    st.header("📝 WordPress Configuration")
    st.info("""
    To publish content to WordPress, you'll need:
    1. Your WordPress site URL (e.g., https://example.com)
    2. Your WordPress username
    3. An application password (NOT your regular WordPress password)

    To generate an application password:
    1. Go to your WordPress Dashboard
    2. Navigate to Users → Security → Application Passwords
    3. Enter a name for your application (e.g., "Content Generator")
    4. Click "Add New Application Password"
    5. Copy the generated password - it will look like: xxxx xxxx xxxx xxxx
    """)

    wp_col1, wp_col2 = st.columns(2)
    with wp_col1:
        wp_url = st.text_input("WordPress URL", help="Enter your WordPress site URL (e.g., https://example.com)")
        wp_username = st.text_input("Username", help="Your WordPress username")
    with wp_col2:
        wp_password = st.text_input("Application Password", type="password", 
                                   help="Generate this in WordPress Dashboard → Users → Security → Application Passwords")
        if st.button("Verify WordPress Connection"):
            if wp_url and wp_username and wp_password:
                try:
                    with st.spinner("Verifying WordPress credentials..."):
                        st.session_state.wordpress_api = WordPressAPI(wp_url, wp_username, wp_password)
                        st.success("✅ WordPress connection successful!")
                except ValueError as e:
                    st.error(f"❌ {str(e)}")
                    st.session_state.wordpress_api = None
                    st.info("""
                    Common authentication issues:
                    1. Make sure you're using the WordPress application password, not your regular login password
                    2. The application password should be in the format: xxxx xxxx xxxx xxxx
                    3. Ensure your WordPress user has the necessary permissions (Author or Editor role)
                    4. Check if the WordPress REST API is enabled on your site
                    """)
                except Exception as e:
                    st.error(f"❌ Error connecting to WordPress: {str(e)}")
                    st.session_state.wordpress_api = None
            else:
                st.warning("Please fill in all WordPress credentials")

    # Feed Management
    st.header("📰 Feed Management")

    # Sample feeds section
    st.markdown("""
    ### Sample RSS Feeds for Testing
    - TechCrunch: https://techcrunch.com/feed/
    - BBC News: http://feeds.bbci.co.uk/news/rss.xml
    - NASA News: https://www.nasa.gov/rss/dyn/breaking_news.rss
    """)

    col1, col2 = st.columns(2)

    with col1:
        feed_name = st.text_input("Feed Name", help="Enter a name to identify this feed")
        feed_url = st.text_input("Feed URL", help="Enter the RSS feed URL (e.g., https://example.com/feed)")

        if st.button("Add Feed"):
            try:
                if not feed_name or not feed_url:
                    st.error("Please provide both feed name and URL")
                else:
                    st.session_state.feed_parser.add_feed(feed_name, feed_url)
                    st.success(f"Added feed: {feed_name}")
            except Exception as e:
                st.error(str(e))

    with col2:
        feeds = st.session_state.feed_parser.get_all_feeds()
        if feeds:
            feed_to_remove = st.selectbox("Select feed to remove", list(feeds.keys()))
            if st.button("Remove Feed"):
                try:
                    st.session_state.feed_parser.remove_feed(feed_to_remove)
                    # Clear feed cache for removed feed
                    if feed_to_remove in st.session_state.feed_cache:
                        del st.session_state.feed_cache[feed_to_remove]
                    st.success(f"Removed feed: {feed_to_remove}")
                except Exception as e:
                    st.error(str(e))

    # Content Generation
    st.header("✨ Content Generation")

    # Cache controls
    cache_col1, cache_col2 = st.columns(2)
    with cache_col1:
        if st.button("Clear Feed Cache"):
            st.session_state.feed_cache = {}
            st.success("Feed cache cleared!")
    with cache_col2:
        if st.button("Clear Content Cache"):
            st.session_state.content_cache = {}
            st.success("Content cache cleared!")

    # Feed selection and parsing
    selected_feed = st.selectbox("Select Feed", list(feeds.keys()) if feeds else [], help="Choose a feed to generate content from")
    if selected_feed and st.button("Fetch Articles"):
        try:
            with st.spinner("Fetching articles..."):
                # Check if feed data is in cache
                if selected_feed in st.session_state.feed_cache:
                    st.session_state.articles = st.session_state.feed_cache[selected_feed]
                    st.success(f"Loaded {len(st.session_state.articles)} articles from cache")
                    st.info("Using cached feed data. Click 'Clear Feed Cache' above to fetch fresh data.")
                else:
                    feed_url = feeds[selected_feed]
                    articles = st.session_state.feed_parser.parse_feed(feed_url)
                    st.session_state.articles = articles
                    # Cache the articles
                    st.session_state.feed_cache[selected_feed] = articles
                    st.success(f"Fetched {len(articles)} articles")
        except Exception as e:
            st.error(str(e))
            st.info("Please make sure you've entered a valid RSS feed URL. You can try one of the sample feeds above.")

    # Article selection and processing
    if 'articles' in st.session_state:
        selected_article = st.selectbox(
            "Select Article",
            options=range(len(st.session_state.articles)),
            format_func=lambda x: st.session_state.articles[x]['title']
        )

        article = st.session_state.articles[selected_article]
        st.subheader("Original Article")
        st.write(article['title'])
        st.write(article['summary'])

        # Keywords input
        keywords = st.text_input("Enter keywords (comma-separated)")
        keyword_list = [k.strip() for k in keywords.split(',')] if keywords else []

        # Create a cache key from article and keywords
        cache_key = f"{article['title']}_{','.join(keyword_list)}"

        if st.button("Generate Content"):
            try:
                # Check if content is in cache
                if cache_key in st.session_state.content_cache:
                    st.session_state.generated_content = st.session_state.content_cache[cache_key]['content']
                    st.session_state.generated_image_url = st.session_state.content_cache[cache_key]['image_url']
                    st.session_state.seo_metrics = st.session_state.content_cache[cache_key]['seo_metrics']
                    st.success("Loaded content from cache")
                    st.info("Using cached content. Click 'Clear Content Cache' above to generate fresh content.")
                else:
                    with st.spinner("Generating content..."):
                        # Generate content
                        content = st.session_state.content_generator.generate_content(article, keyword_list)
                        content_dict = json.loads(content)
                        st.session_state.generated_content = content_dict

                        # Generate image
                        image_prompt = st.session_state.content_generator.generate_image_prompt(content_dict)
                        image_url = st.session_state.content_generator.generate_image(image_prompt)
                        st.session_state.generated_image_url = image_url

                        # Analyze SEO
                        seo_metrics = st.session_state.seo_optimizer.analyze_content(
                            content_dict,
                            keyword_list
                        )
                        st.session_state.seo_metrics = seo_metrics

                        # Cache the generated content
                        st.session_state.content_cache[cache_key] = {
                            'content': content_dict,
                            'image_url': image_url,
                            'seo_metrics': seo_metrics
                        }

                    st.success("Content generated successfully!")
            except Exception as e:
                st.error(f"Error generating content: {str(e)}")

    # Preview and Publish
    if 'generated_content' in st.session_state:
        st.header("👁️ Preview and Publish")

        # Display generated content
        st.subheader("Generated Content")
        st.write(st.session_state.generated_content['title'])
        if 'generated_image_url' in st.session_state:
            st.image(st.session_state.generated_image_url)
        st.write(st.session_state.generated_content['content'])

        # Display SEO metrics
        st.subheader("SEO Analysis")
        metrics = st.session_state.seo_metrics
        st.write(f"Word count: {metrics['word_count']}")
        st.write(f"Readability score: {metrics['readability_score']:.2f}")
        st.write("Keyword density:")
        for keyword, density in metrics['keyword_density'].items():
            st.write(f"- {keyword}: {density:.2%}")
        if metrics['suggestions']:
            st.write("Suggestions:")
            for suggestion in metrics['suggestions']:
                st.write(f"- {suggestion}")

        # Test mode option
        test_mode = st.checkbox("Test Mode (Skip image upload)", 
                              help="Enable this to skip image upload when testing WordPress integration")

        # Publish options
        if st.button("Publish to WordPress"):
            if st.session_state.wordpress_api is None:
                st.error("⚠️ Please configure and verify WordPress settings at the top of the page first")
                st.info("Scroll to the top to find the WordPress Configuration section")
            else:
                try:
                    with st.spinner("Publishing to WordPress..."):
                        # Upload image only if not in test mode
                        if not test_mode and 'generated_image_url' in st.session_state:
                            st.info("Uploading image... (Disable Test Mode to skip this step)")
                            media = st.session_state.wordpress_api.upload_media(
                                st.session_state.generated_image_url
                            )
                            # Add image to content
                            content = st.session_state.generated_content
                            content['content'] = f'<img src="{media["source_url"]}" alt="{content["title"]}">\n\n' + content['content']
                        else:
                            content = st.session_state.generated_content

                        # Create post
                        post = st.session_state.wordpress_api.create_post(content)
                        st.success(f"Published successfully! Post ID: {post['id']}")
                        st.markdown(f"[View Post]({post['link']})")
                except Exception as e:
                    st.error(f"Error publishing to WordPress: {str(e)}")
                    st.info("Please make sure your WordPress credentials are correct and you have sufficient permissions.")

    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ by AI Content Generator")


elif st.session_state.page == "site management":
    st.title("Site Management")

    # Site Configuration
    site_name = st.text_input("Site Name")
    if site_name:
        if site_name not in st.session_state.site_config:
            st.session_state.site_config[site_name] = {}

        # WordPress Configuration
        st.header("WordPress Configuration")
        wp_url = st.text_input("WordPress URL", 
                              value=st.session_state.site_config[site_name].get('wp_url', ''))
        wp_username = st.text_input("Username",
                                  value=st.session_state.site_config[site_name].get('wp_username', ''))
        wp_password = st.text_input("Application Password", type="password")

        if st.button("Save WordPress Configuration"):
            try:
                # Create and verify WordPress API instance
                new_wp_api = WordPressAPI(
                    wp_url,
                    wp_username,
                    wp_password if wp_password else st.session_state.site_config[site_name].get('wp_password', '')
                )
                
                # If verification successful, update config
                st.session_state.site_config[site_name].update({
                    'wp_url': wp_url,
                    'wp_username': wp_username,
                    'wp_password': wp_password if wp_password else st.session_state.site_config[site_name].get('wp_password', '')
                })
                
                # Store verified API instance
                st.session_state.wordpress_api = new_wp_api
                
                st.success("✅ WordPress configuration saved and verified!")
            except Exception as e:
                st.error(f"❌ Error saving WordPress configuration: {str(e)}")

        # RSS Feed Configuration
        st.header("RSS Feed Configuration")
        feed_urls = st.text_area("RSS Feed URLs (one per line)", 
                               value='\n'.join(st.session_state.site_config[site_name].get('feed_urls', [])))
        posts_per_feed = st.number_input("Posts to fetch per feed", min_value=1, value=5)

        if st.button("Save RSS Configuration"):
            st.session_state.site_config[site_name].update({
                'feed_urls': [url.strip() for url in feed_urls.split('\n') if url.strip()],
                'posts_per_feed': posts_per_feed
            })
            st.success("RSS configuration saved!")

elif st.session_state.page == "bulk article generator":
    st.title("Bulk Article Generator")

    # Site Selection
    if not st.session_state.site_config:
        st.warning("Please configure at least one site in Site Management first.")
    else:
        selected_site = st.selectbox("Select Site", list(st.session_state.site_config.keys()))
        config = st.session_state.site_config[selected_site]

        if st.button("Fetch Articles"):
            with st.spinner("Fetching articles from RSS feeds..."):
                all_articles = []
                for feed_url in config['feed_urls']:
                    articles = st.session_state.feed_parser.parse_feed(feed_url)
                    all_articles.extend(articles[:config['posts_per_feed']])
                st.session_state.articles = all_articles
                st.success(f"Fetched {len(all_articles)} articles")

        if 'articles' in st.session_state:
            selected_articles = st.multiselect(
                "Select articles to process",
                options=range(len(st.session_state.articles)),
                format_func=lambda x: st.session_state.articles[x]['title']
            )

            if selected_articles:
                if st.button("Generate Hindi Content"):
                    with st.spinner("Generating Hindi content..."):
                        for idx in selected_articles:
                            article = st.session_state.articles[idx]
                            content_str = st.session_state.content_generator.generate_hindi_content(article)
                            content = json.loads(content_str)

                            # Check if WordPress config exists
                            if not all(key in config for key in ['wp_url', 'wp_username', 'wp_password']):
                                st.error("Please configure WordPress settings in Site Management first")
                                continue

                            # Initialize WordPress API if needed
                            try:
                                if not st.session_state.wordpress_api:
                                    st.session_state.wordpress_api = WordPressAPI(
                                        config['wp_url'],
                                        config['wp_username'],
                                        config['wp_password']
                                    )
                            except Exception as e:
                                st.error(f"WordPress connection error: {str(e)}")
                                continue

                            # Post to WordPress
                            try:
                                post = st.session_state.wordpress_api.create_post(content)
                                st.success(f"Published: {content['title']}")
                            except Exception as e:
                                st.error(f"Error publishing article: {str(e)}")