"""
比特币价格追踪应用
"""

import streamlit as st
import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
import logging
import datetime

# 配置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_number_with_commas(number):
    """
    格式化数字，添加千位分隔符
    """
    return '{:,.2f}'.format(number)

def format_percentage(percentage):
    """
    格式化百分比字符串，在涨跌时显示绿色/红色
    使用Streamlit的proper syntax for color
    """
    if percentage is None:
        return "N/A"

    if percentage >= 0:
        # 根据Streamlit文档，语法可能为st.markdown配合colored text
        return f"<span style='color:green'>+{percentage:.2f}%</span>"
    else:
        return f"<span style='color:red'>{percentage:.2f}%</span>"

# Streamlit wrappers to support formatted text
def colored_markdown(text, color):
    return f"<span style='color:{color}'>{text}</span>"

def colored_metric(metric_value, color):
    # Correctly formatted metric with color
    if isinstance(metric_value, float):
        return colored_markdown(f"{metric_value:.2f}", color)
    return metric_value

def get_bitcoin_price():
    """
    从CoinGecko API获取比特币价格信息
    返回包含当前价格和24小时变化数据的字典
    """
    try:
        response = requests.get("https://api.coingecko.com/api/v3/coins/bitcoin", timeout=5)
        response.raise_for_status()
        data = response.json()

        return {
            'current_price': data['market_data']['current_price']['usd'],
            'price_change_percentage': data['market_data']['price_change_percentage_24h'] or 0,
            'timestamp': datetime.datetime.now().timestamp()
        }
    except requests.exceptions.Timeout:
        logger.error("网络请求超时，请检查您的网络连接")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"获取比特币价格时出错: {e}")
        return None

def get_bitcoin_price_history():
    """
    从CoinGecko API获取比特币最近24小时的价格历史数据
    返回包含时间序列数据的DataFrame
    """
    try:
        response = requests.get(
            "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1&interval=hourly",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        prices = data['prices']
        prices = [p/1000 for p in prices]  # Convert to seconds timestamp
        market_caps = data['total_volumes'] if 'total_volumes' in data else data['market_caps']

        # Prepare the dataframe
        data_list = []
        for i in range(len(prices)):
            ts = datetime.datetime.fromtimestamp(prices[i])
            data_list.append({
                'time': ts.strftime('%H:%M'),
                'price': data['prices'][i][1],
                'volume': market_caps[i] or 0 if market_caps else 0
            })

        df = pd.DataFrame(data_list)

        # Set time as index
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)

        return df
    except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        logger.error(f"获取价格历史数据时出错: {e}")
        return None

def setup_cache():
    """
    初始化会话状态缓存变量
    """
    if 'price_data' not in st.session_state:
        st.session_state.price_data = None

    if 'history_data' not in st.session_state:
        st.session_state.history_data = None

    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()

    if 'loading' not in st.session_state:
        st.session_state.loading = False

    if 'price_error' not in st.session_state:
        st.session_state.price_error = None

    if 'history_error' not in st.session_state:
        st.session_state.history_error = None

def get_data_with_spinner(refresh_func, *args, **kwargs):
    """
    使用spinner执行数据获取函数，统一处理加载状态和错误
    """
    st.session_state.loading = True

    try:
        with st.spinner("正在获取最新数据中..."):
            result = refresh_func(*args, **kwargs)

            if result is None:
                raise Exception("无法获取数据")

            return result

    except Exception as e:
        st.session_state.loading = False
        logger.error(f"数据加载失败: {e}")
        st.error(f"数据加载失败: {e}")
        return None
    finally:
        st.session_state.loading = False

def refresh_price_data():
    """
    刷新比特币价格数据
    """
    if st.session_state.price_data is None or pd.isna(st.session_state.price_data):
        st.session_state.price_error = None
        result = get_bitcoin_price()
        if result:
            st.session_state.price_data = result
            st.session_state.last_update = time.time()
            return True

    # 检查是否需要更新数据
    time_diff = time.time() - st.session_state.last_update
    if time_diff >= 60:  # 每分钟更新一次
        result = get_bitcoin_price()
        if result:
            st.session_state.price_data = result
            return True

    return False

def refresh_history_data():
    """
    刷新比特币历史价格数据
    """
    if st.session_state.history_data is None or pd.isna(st.session_state.history_data):
        result = get_bitcoin_price_history()
        if result:
            st.session_state.history_data = result
            return True

    # 根据价格数据刷新间隔更新历史数据
    time_diff = time.time() - st.session_state.last_update
    if time_diff >= 120:  # 每2分钟更新一次
        result = get_bitcoin_price_history()
        if result:
            st.session_state.history_data = result
            return True

    return False

def main():
    # 设置页面配置
    st.set_page_config(
        page_title="比特币价格追踪器",
        page_icon="₿",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

    # 应用标题和描述
    st.title("💰 比特币价格追踪器")
    st.markdown("""
    ## 实时比特币价格追踪
    简洁易用的比特币价格显示器，提供实时价格和历史趋势
    """)

    # 页面布局
    col1, col2 = st.columns([1, 1])

    # 初始化缓存变量
    setup_cache()

    # 添加UI控制元素和数据刷新
    st.subheader("⚙️ 设置")

    with st.expander("高级设置", expanded=False):
        refresh_period = st.slider(
            "数据刷新间隔(秒)",
            min_value=30,
            max_value=300,
            value=120,
            help="调整应用数据刷新的频率"
        )

        # 默认每3秒更新一次，但实际实现可以根据需要调整
        # 在实际应用中，我们使用滑块控制的刷新间隔
        st.info(f"当前刷新间隔: {refresh_period} 秒")

    # 手动刷新按钮
    if st.button("🔄 手动刷新价格", use_container_width=True):
        # 使用spinner刷新所有数据
        result = get_data_with_spinner(lambda: (refresh_price_data(), refresh_history_data()))
        if result:
            st.success("数据已更新!", icon="✅")

    # 定期自动刷新
    auto_refresh = st.checkbox("启用自动刷新", value=True)

    # 检查是否需要自动刷新
    if auto_refresh and not st.session_state.loading:
        time_diff = time.time() - st.session_state.last_update

        if time_diff >= st.session_state.get('refresh_interval', 60):
            get_data_with_spinner(lambda: (refresh_price_data(), refresh_history_data()))

    # 显示加载状态
    if st.session_state.loading:
        with col1:
            st.write("🔄 数据正在加载中...")

    # 保存到文件的功能
    col_last, col_refresh = st.columns([3, 1])
    with col_refresh:
        st.button("💾 保存数据", on_click=lambda: st.download_button(
            label="下载数据",
            data=str(st.session_state.price_data),
            file_name="bitcoin_data.txt",
            mime="text/plain"
        ))

    # 显示价格数据
    if st.session_state.price_data:
        with col1:
            st.subheader("📊 当前价格")

            # 格式化价格显示
            price = st.session_state.price_data['current_price']
            change_percentage = st.session_state.price_data['price_change_percentage']

            col_price, col_stats = st.columns(2)

            with col_price:
                # 当前价格卡片
                st.info(f"当前价格")
                st.markdown(f"""
                <div style='background:#f0f0f0; padding:15px; border-radius:8px'>
                    <h4>₿ {format_number_with_commas(price)}</h4>
                    <p>{format_percentage(change_percentage)}</p>
                </div>
                """, unsafe_allow_html=True)

                # 显示更新时间
                if st.session_state.price_data['timestamp']:
                    update_time = datetime.datetime.fromtimestamp(
                        st.session_state.price_data['timestamp']
                    ).strftime('%Y-%m-%d %H:%M:%S')
                    st.caption(f"更新于: {update_time}")

            with col_stats:
                st.subheader("📈 统计信息")
                col_cap, col_vol = st.columns(2)
                col_cap.metric("市值", format_number_with_commas(1.38e12))
                col_vol.metric("24h交易量", format_number_with_commas(2.85e10))

        with col2:
            st.subheader("📈 24小时价格走势")

            if st.session_state.history_data is not None and not st.session_state.history_data.empty:
                fig, ax = plt.figure(figsize=(6, 4))

                # 创建更密集的价格点
                filtered_data = st.session_state.history_data.resample('2H').last()

                # 绘制价格趋势
                ax.plot(filtered_data.index, filtered_data['price'], color='#2a9d8f', linewidth=2)

                # 标记最高和最低点
                max_price = st.session_state.history_data['price'].max()
                min_price = st.session_state.history_data['price'].min()

                if not st.session_state.history_data.empty:
                    # 添加标记
                    if len(filtered_data[filtered_data['price'] == max_price]) > 0:
                        ax.plot(filtered_data.index[filtered_data['price'] == max_price],
                               [max_price], 'ro', markersize=8)

                        # 添加标记说明
                        ax.annotate(f"${format_number_with_commas(max_price)}",
                                   xy=(filtered_data.index[filtered_data['price'] == max_price][0], max_price),
                                   fontsize=9)

                    if len(filtered_data[filtered_data['price'] == min_price]) > 0:
                        ax.plot(filtered_data.index[filtered_data['price'] == min_price],
                               [min_price], 'go', markersize=8)

                        # 添加标记说明
                        ax.annotate(f"${format_number_with_commas(min_price)}",
                                   xy=(filtered_data.index[filtered_data['price'] == min_price][0], min_price),
                                   fontsize=9, color='green')

                # 添加移动平均线（7小时）
                if len(filtered_data) >= 7:
                    filtered_data.sort_index(inplace=True)
                    filtered_data['7h_rolling'] = filtered_data['price'].rolling(window=5).mean()
                    ax.plot(filtered_data.index, filtered_data['7h_rolling'], 'b--', alpha=0.5, label='5h 移动平均')
                    ax.legend(loc='upper left')

                # 设置图表样式
                ax.set_title('比特币24小时价格走势', fontsize=10)
                ax.set_xlabel('时间')
                ax.set_ylabel('价格 (USD)')
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.set_ylim(min_price * 0.9, max_price * 1.1)

                # 显示平均价格线
                avg_price = filtered_data['price'].mean()
                ax.axhline(y=avg_price, color='purple', linestyle='--', alpha=0.6)
                ax.annotate(f"${format_number_with_commas(avg_price)}",
                           xy=(filtered_data.index[-1], avg_price),
                           fontsize=8, color='purple')

                st.pyplot(fig)
            else:
                st.warning("无法加载价格历史数据，请刷新页面重试")
    else:
        # 显示空状态提示
        st.write("#### 比特币数据")
        st.info("数据正在加载中，请稍候...")
        st.write("刷新应用或手动点击刷新按钮以获取数据")

if __name__ == "__main__":
    main()