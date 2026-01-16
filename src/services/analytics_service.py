"""
Analytics Service - Premium Business Intelligence Dashboard
Advanced insights with Plotly interactive charts
"""

from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.database import get_books, get_sales, get_stats
from src.ui.components import render_page_header, render_section_header
from src.utils.helpers import get_low_stock_books, group_sales_by_bundle


def render_analytics_page():
    """Main analytics dashboard with comprehensive insights."""
    render_page_header(
        "Business Intelligence Dashboard",
        "Comprehensive insights into your sales performance, inventory health, and growth metrics"
    )

    # Get fresh data
    stats = get_stats()
    all_sales = get_sales()
    all_books = get_books()
    grouped_sales = group_sales_by_bundle(all_sales)

    # Calculate core metrics
    metrics = _calculate_core_metrics(grouped_sales, stats)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== TOP METRICS CARDS =====
    _render_hero_metrics(metrics)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ===== FINANCIAL OVERVIEW (REDUCED) =====
    _render_financial_overview(metrics, stats)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== REVENUE TIMELINE (PLOTLY INTERACTIVE) =====
    _render_revenue_timeline(all_sales)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== DETAILED INSIGHTS =====
    tab1, tab2, tab3 = st.tabs([
        "🏆 Best Performers",
        "📦 Inventory Health",
        "💰 Profit Analysis"
    ])

    with tab1:
        _render_best_performers(all_sales, all_books)

    with tab2:
        _render_inventory_health(stats, all_books)

    with tab3:
        _render_profit_analysis(grouped_sales, all_books)


# ============================================================================
# CORE METRICS CALCULATION
# ============================================================================
def _calculate_core_metrics(grouped_sales, stats):
    """Calculate all core business metrics."""
    total_revenue = sum(s["total"] for s in grouped_sales)
    total_items = sum(s["qty"] for s in grouped_sales)
    total_profit = sum(s['profit'] for s in grouped_sales)
    num_transactions = len(grouped_sales)
    bundles_count = len([s for s in grouped_sales if s['type'] == 'bundle'])
    single_sales_count = num_transactions - bundles_count

    avg_order_value = total_revenue / num_transactions if num_transactions > 0 else 0
    avg_books_per_order = total_items / num_transactions if num_transactions > 0 else 0
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    # Weekly comparison
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)

    this_week_sales = [s for s in grouped_sales if _parse_sale_date(s) >= week_ago]
    last_week_sales = [s for s in grouped_sales if two_weeks_ago <= _parse_sale_date(s) < week_ago]

    this_week_revenue = sum(s["total"] for s in this_week_sales)
    last_week_revenue = sum(s["total"] for s in last_week_sales)

    # ✅ FIXED: Handle zero division properly
    if last_week_revenue == 0 and this_week_revenue == 0:
        revenue_growth = 0
        revenue_growth_text = "No sales"
    elif last_week_revenue == 0 and this_week_revenue > 0:
        revenue_growth = None  # Infinite growth
        revenue_growth_text = "NEW 🎉"
    elif this_week_revenue == 0 and last_week_revenue > 0:
        revenue_growth = -100
        revenue_growth_text = "-100%"
    else:
        revenue_growth = ((this_week_revenue - last_week_revenue) / last_week_revenue) * 100
        revenue_growth_text = f"{revenue_growth:+.1f}%"

    return {
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_items': total_items,
        'num_transactions': num_transactions,
        'bundles_count': bundles_count,
        'single_sales_count': single_sales_count,
        'avg_order_value': avg_order_value,
        'avg_books_per_order': avg_books_per_order,
        'profit_margin': profit_margin,
        'this_week_revenue': this_week_revenue,
        'last_week_revenue': last_week_revenue,
        'revenue_growth': revenue_growth,
        'revenue_growth_text': revenue_growth_text,  # ✅ New field
        'inventory_value': stats['stock_value'],
        'potential_revenue': stats['potential_revenue'],
    }


def _parse_sale_date(sale):
    """Parse sale date to date object."""
    try:
        date_str = sale.get("date", "")
        if '/' in date_str:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        elif ' ' in date_str:
            return datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
        else:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return datetime.now().date()


# ============================================================================
# HERO METRICS CARDS
# ============================================================================
def _render_hero_metrics(metrics):
    """Render top-level KPI cards with gradients and comparisons."""
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if metrics['revenue_growth'] is None or metrics['revenue_growth_text'] == "NEW 🎉":
            growth_icon = "🎉"
            growth_text = metrics['revenue_growth_text']
        elif metrics['revenue_growth'] >= 0:
            growth_icon = "📈"
            growth_text = f"{metrics['revenue_growth']:+.1f}% vs last week"
        else:
            growth_icon = "📉"
            growth_text = f"{metrics['revenue_growth']:.1f}% vs last week"

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);">
                <h3 style="margin: 0; font-size: 28px;">💰</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px;">TOTAL REVENUE</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">€{metrics['total_revenue']:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 11px; opacity: 0.85; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; display: inline-block;">
                    {growth_icon} {growth_text}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 20px rgba(67, 233, 123, 0.4);">
                <h3 style="margin: 0; font-size: 28px;">📈</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px;">NET PROFIT</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">€{metrics['total_profit']:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 11px; opacity: 0.85; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; display: inline-block;">
                    Margin: {metrics['profit_margin']:.1f}%
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 20px rgba(250, 112, 154, 0.4);">
                <h3 style="margin: 0; font-size: 28px;">📚</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px;">BOOKS SOLD</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">{metrics['total_items']}</h2>
                <p style="margin: 8px 0 0 0; font-size: 11px; opacity: 0.85; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; display: inline-block;">
                    Avg: {metrics['avg_books_per_order']:.1f} per order
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 20px rgba(79, 172, 254, 0.4);">
                <h3 style="margin: 0; font-size: 28px;">🛒</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px;">TRANSACTIONS</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">{metrics['num_transactions']}</h2>
                <p style="margin: 8px 0 0 0; font-size: 11px; opacity: 0.85; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; display: inline-block;">
                    {metrics['bundles_count']} bundles • {metrics['single_sales_count']} singles
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col5:
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 20px; border-radius: 12px; text-align: center; color: white;
                        box-shadow: 0 8px 20px rgba(240, 147, 251, 0.4);">
                <h3 style="margin: 0; font-size: 28px;">💳</h3>
                <p style="margin: 8px 0; font-size: 11px; opacity: 0.9; font-weight: 600; letter-spacing: 1px;">AVG ORDER</p>
                <h2 style="margin: 5px 0; font-size: 24px; font-weight: 700;">€{metrics['avg_order_value']:.2f}</h2>
                <p style="margin: 8px 0 0 0; font-size: 11px; opacity: 0.85; background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; display: inline-block;">
                    Per transaction
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ============================================================================
# FINANCIAL OVERVIEW
# ============================================================================
def _render_financial_overview(metrics, stats):
    """Render simplified financial overview section."""
    render_section_header("Financial Overview", "💼")

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.metric(
            "📦 Inventory Value",
            f"€{metrics['inventory_value']:.2f}",
            help="Total cost of current stock (no packaging)"
        )

    with col2:
        st.metric(
            "🎯 Potential Revenue",
            f"€{metrics['potential_revenue']:.2f}",
            help="If all stock sells at target price"
        )


# ============================================================================
# ✅ PLOTLY REVENUE TIMELINE WITH DYNAMIC LABELS
# ============================================================================
def _render_revenue_timeline(all_sales):
    """Render interactive Plotly timeline with period selector."""
    render_section_header("Revenue & Profit Timeline", "📈")

    if not all_sales:
        st.info("📭 No sales data available yet")
        return

    # ✅ TIME PERIOD SELECTOR
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        view_mode = st.selectbox(
            "📅 View",
            ["Daily", "Weekly", "Monthly"],
            key="timeline_view"
        )

    # Aggregate by date
    sales_by_date = defaultdict(lambda: {
        'revenue': 0,
        'profit': 0,
        'orders': set(),
        'books': 0
    })

    for s in all_sales:
        try:
            date_str = s["date"]
            if '/' in date_str:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            elif ' ' in date_str:
                date_obj = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            else:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")

            # Group by selected period
            if view_mode == "Daily":
                period_key = date_obj.date()
            elif view_mode == "Weekly":
                week_start = date_obj.date() - timedelta(days=date_obj.weekday())
                period_key = week_start
            else:  # Monthly
                period_key = date_obj.date().replace(day=1)

        except:
            continue

        # Calculate profit for this sale
        from src.core.calculations import calculate_sale_profit
        from src.data.database import get_books
        books = {b['id']: b for b in get_books()}
        book = books.get(s['book_id'])

        if book:
            calc = calculate_sale_profit(
                qty=s['qty'],
                total_paid=s['total'],
                packaging_per_book=s['packaging_per_book'],
                buy_price=book['buy_price']
            )
            profit = calc['profit']
        else:
            profit = 0

        sales_by_date[period_key]['revenue'] += s['total']
        sales_by_date[period_key]['profit'] += profit
        sales_by_date[period_key]['orders'].add(s.get('bundle_id') or s['id'])
        sales_by_date[period_key]['books'] += s['qty']

    # Convert to sorted data
    sorted_data = sorted(sales_by_date.items())

    dates = []
    revenues = []
    profits = []
    orders_list = []
    books_list = []

    for period, data in sorted_data:
        # Format period label
        if view_mode == "Daily":
            period_label = period.strftime("%d/%m/%Y")
        elif view_mode == "Weekly":
            period_label = f"Week of {period.strftime('%d/%m/%Y')}"
        else:  # Monthly
            period_label = period.strftime("%B %Y")

        dates.append(period_label)
        revenues.append(round(data['revenue'], 2))
        profits.append(round(data['profit'], 2))
        orders_list.append(len(data['orders']))
        books_list.append(data['books'])

    # ✅ DYNAMIC METRIC LABELS
    if view_mode == "Daily":
        metric_prefix = "All-Time"
    elif view_mode == "Weekly":
        metric_prefix = "All Weeks"
    else:
        metric_prefix = "All Months"

    # Summary metrics
    total_revenue = sum(revenues)
    total_profit = sum(profits)
    total_orders = sum(orders_list)
    total_books = sum(books_list)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            f"💰 {metric_prefix} Revenue",
            f"€{total_revenue:.2f}",
            help=f"Total revenue across all {view_mode.lower()} periods"
        )
    with col2:
        st.metric(
            f"📈 {metric_prefix} Profit",
            f"€{total_profit:.2f}",
            help=f"Total profit across all {view_mode.lower()} periods"
        )
    with col3:
        st.metric(
            "🛒 Total Orders",
            total_orders,
            help="Total number of transactions"
        )
    with col4:
        st.metric(
            "📚 Books Sold",
            total_books,
            help="Total books sold"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ✅ PLOTLY REVENUE & PROFIT CHART
    fig_revenue = go.Figure()

    # Revenue trace (area)
    fig_revenue.add_trace(go.Scatter(
        x=dates,
        y=revenues,
        name='Revenue',
        mode='lines+markers',
        line=dict(color='#667eea', width=3),
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)',
        marker=dict(size=8, symbol='circle'),
        hovertemplate='<b>%{x}</b><br>' +
                      'Revenue: €%{y:.2f}<br>' +
                      '<extra></extra>'
    ))

    # Profit trace (line)
    fig_revenue.add_trace(go.Scatter(
        x=dates,
        y=profits,
        name='Profit',
        mode='lines+markers',
        line=dict(color='#43e97b', width=2, dash='dot'),
        marker=dict(size=6, symbol='diamond'),
        hovertemplate='<b>%{x}</b><br>' +
                      'Profit: €%{y:.2f}<br>' +
                      '<extra></extra>'
    ))

    fig_revenue.update_layout(
        title=f"<b>📊 {view_mode} Revenue & Profit Trends</b>",
        xaxis_title=f"<b>{view_mode} Period</b>",
        yaxis_title="<b>Amount (€)</b>",
        height=400,
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60, r=20, t=60, b=60)
    )

    fig_revenue.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        tickangle=-45
    )

    fig_revenue.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )

    st.plotly_chart(fig_revenue, width='stretch')

    st.markdown("<br>", unsafe_allow_html=True)

    # ✅ PLOTLY ORDERS BAR CHART
    fig_orders = go.Figure()

    fig_orders.add_trace(go.Bar(
        x=dates,
        y=orders_list,
        name='Orders',
        marker=dict(
            color=orders_list,
            colorscale=[[0, '#fa709a'], [1, '#fee140']],
            showscale=False
        ),
        text=orders_list,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>' +
                      'Orders: %{y}<br>' +
                      f'Books: {books_list[0]}<br>' +
                      '<extra></extra>',
        customdata=books_list
    ))

    # Update hover to show books
    fig_orders.update_traces(
        hovertemplate='<b>%{x}</b><br>' +
                      'Orders: %{y}<br>' +
                      'Books: %{customdata}<br>' +
                      '<extra></extra>'
    )

    fig_orders.update_layout(
        title=f"<b>📦 {view_mode} Orders</b>",
        xaxis_title=f"<b>{view_mode} Period</b>",
        yaxis_title="<b>Number of Orders</b>",
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Arial", size=12),
        showlegend=False,
        margin=dict(l=60, r=20, t=60, b=60)
    )

    fig_orders.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        tickangle=-45
    )

    fig_orders.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)'
    )

    st.plotly_chart(fig_orders, width='stretch')


# ============================================================================
# BEST PERFORMERS TAB
# ============================================================================
def _render_best_performers(all_sales, all_books):
    """Render best performing books - quantity only."""
    render_section_header("Best Selling Books", "🏆")

    if not all_sales:
        st.info("📭 No sales to analyze")
        return

    # Aggregate book sales
    book_performance = defaultdict(lambda: {'qty': 0})
    book_map = {b['id']: b for b in all_books}

    for s in all_sales:
        book_id = s['book_id']
        book_performance[book_id]['qty'] += s['qty']

    # Create leaderboard
    leaderboard = []
    for book_id, perf in book_performance.items():
        book = book_map.get(book_id, {})
        leaderboard.append({
            'Title': book.get('title', 'Unknown')[:50],
            'Author': book.get('author', '')[:30],
            'Sold': perf['qty']
        })

    leaderboard.sort(key=lambda x: x['Sold'], reverse=True)

    # Display top 10
    for i, book in enumerate(leaderboard[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"

        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{medal} {book['Title']}**")
                st.caption(f"by {book['Author']}")
            with col2:
                st.metric("Quantity Sold", book['Sold'], label_visibility="collapsed")
            st.divider()


# ============================================================================
# INVENTORY HEALTH TAB
# ============================================================================
def _render_inventory_health(stats, all_books):
    """Render inventory health metrics and alerts with book IDs."""
    render_section_header("Inventory Status", "📦")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📚 Total Books", stats['book_count'])
    with col2:
        st.metric("✅ Active", stats['active_count'])
        st.caption(f"{stats['active_count']/stats['book_count']*100:.0f}% of total inventory")
    with col3:
        st.metric("🔴 Sold Out", stats['sold_count'])
    with col4:
        st.metric("📦 Total Stock", stats['total_stock'])

    st.markdown("<br>", unsafe_allow_html=True)

    # Low stock alerts WITH BOOK ID
    low_stock = get_low_stock_books()

    if low_stock:
        st.warning(f"⚠️ **{len(low_stock)} book(s)** need restocking")

        for book in low_stock:
            with st.expander(f"{'🔴' if book['stock'] == 1 else '🟡'} {book['id']} - {book['title']}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption("📖 Book ID")
                    st.write(f"**{book['id']}**")
                with col2:
                    st.caption("✍️ Author")
                    st.write(book['author'])
                with col3:
                    st.caption("📦 Stock")
                    st.write(f"**{book['stock']}** remaining")
                with col4:
                    st.caption("💰 Value")
                    st.write(f"€{book['buy_price']:.2f}")
    else:
        st.success("✅ All stock levels healthy!")

    # Below cost books WITH BOOK ID
    if stats['low_margin_books']:
        st.markdown("<br>", unsafe_allow_html=True)
        st.error(f"💔 **{len(stats['low_margin_books'])} book(s)** priced below cost")

        # Get book map to find IDs
        book_map = {b['title']: b['id'] for b in all_books}

        for b in stats['low_margin_books']:
            loss = b['buy'] - b['target']
            book_id = book_map.get(b['title'], 'N/A')

            with st.expander(f"⚠️ {book_id} - {b['title']}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption("📖 Book ID")
                    st.write(f"**{book_id}**")
                with col2:
                    st.caption("💵 Buy Price")
                    st.write(f"€{b['buy']:.2f}")
                with col3:
                    st.caption("🎯 Target Price")
                    st.write(f"€{b['target']:.2f}")
                with col4:
                    st.caption("💸 Loss")
                    st.write(f"€{loss:.2f}")


# ============================================================================
# ✅ PROFIT ANALYSIS WITH PROPER CARD RENDERING
# ============================================================================
def _render_profit_analysis(grouped_sales, all_books):
    """Render detailed profit analysis with 5% granularity."""
    render_section_header("Profit Breakdown", "💰")

    if not grouped_sales:
        st.info("📭 No sales data")
        return

    # ✅ CREATE 5% MARGIN BUCKETS
    margin_buckets = {}

    # Negative margins (losses)
    for i in range(-100, 0, 5):
        margin_buckets[f"{i}% to {i+5}%"] = 0

    # Positive margins
    for i in range(0, 100, 5):
        margin_buckets[f"{i}% to {i+5}%"] = 0

    # 100%+ (extreme profits)
    margin_buckets["100%+"] = 0

    # Categorize sales
    for s in grouped_sales:
        profit = s['profit']
        revenue = s['total']

        if revenue > 0:
            margin = (profit / revenue) * 100

            # Find appropriate bucket
            if margin >= 100:
                margin_buckets["100%+"] += 1
            else:
                bucket_index = int(margin // 5) * 5
                bucket_key = f"{bucket_index}% to {bucket_index+5}%"
                if bucket_key in margin_buckets:
                    margin_buckets[bucket_key] += 1

    # Filter out empty buckets and sort
    active_buckets = {k: v for k, v in margin_buckets.items() if v > 0}
    sorted_buckets = dict(sorted(active_buckets.items(), key=lambda x: x[1], reverse=True))

    # ✅ NATIVE BAR CHART
    st.markdown("**📊 Sales Distribution by Profit Margin (5% Increments)**")

    df_margins = pd.DataFrame({
        'Margin Range': list(sorted_buckets.keys()),
        'Sales Count': list(sorted_buckets.values())
    }).set_index('Margin Range')

    st.bar_chart(df_margins, color="#667eea", height=350, horizontal=True)

    # ✅ MOST PROFITABLE SALES - USING COLUMNS (NO HTML)
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_section_header("Most Profitable Sales", "💎")

    top_profitable = sorted(grouped_sales, key=lambda x: x['profit'], reverse=True)[:10]

    for i, s in enumerate(top_profitable, 1):
        margin = (s['profit'] / s['total'] * 100) if s['total'] > 0 else 0

        # Determine color and icon
        if margin < 0:
            icon = "💔"
            color = "#ff6b6b"
        elif margin < 20:
            icon = "⚠️"
            color = "#feca57"
        elif margin < 40:
            icon = "💙"
            color = "#4facfe"
        else:
            icon = "💚"
            color = "#43e97b"

        # Sale title
        if s['type'] == 'bundle':
            title = f"📦 Bundle ({s['qty']} books)"
        else:
            title = s.get('book_title', 'Unknown')[:40]

        # Format date
        try:
            date_str = s.get('date', 'N/A')
            if '-' in date_str and len(date_str) == 10:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = date_obj.strftime("%d/%m/%Y")
            else:
                display_date = date_str
        except:
            display_date = s.get('date', 'N/A')

        # ✅ RENDER WITH COLUMNS (NO HTML ISSUES)
        with st.container():
            col1, col2, col3 = st.columns([5, 2, 2])

            with col1:
                st.markdown(f"**{icon} #{i} {title}**")
                st.caption(f"`{display_date}` • {s.get('platform', 'Unknown')}")

            with col2:
                st.metric("Profit", f"€{s['profit']:.2f}", label_visibility="collapsed")

            with col3:
                st.metric("Margin", f"{margin:+.1f}%", label_visibility="collapsed")

            # Add colored bar indicator
            st.markdown(
                f'<div style="height: 4px; background: {color}; border-radius: 2px; margin-top: -10px;"></div>',
                unsafe_allow_html=True
            )

            st.divider()


# ============================================================================
# HOME PAGE OVERVIEW
# ============================================================================
def get_overview_stats() -> dict:
    """Get overview stats for home page."""
    stats = get_stats()
    all_sales = get_sales()

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)

    weekly_sales = []

    for s in all_sales:
        try:
            date_str = s['date']

            if '/' in date_str:
                sale_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            elif ' ' in date_str:
                sale_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
            else:
                sale_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            in_range = week_ago <= sale_date <= today

            if in_range:
                weekly_sales.append(s)

        except Exception:
            continue

    weekly_revenue = sum(s['total'] for s in weekly_sales)

    return {
        'book_count': stats['book_count'],
        'active_count': stats['active_count'],
        'revenue': stats['revenue'],
        'profit': stats['profit'],
        'weekly_sales': len(weekly_sales),
        'weekly_revenue': weekly_revenue,
        'low_stock_count': len(get_low_stock_books())
    }
