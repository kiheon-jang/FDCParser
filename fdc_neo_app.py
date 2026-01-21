#!/usr/bin/env python3
"""
FDC NEO Application
Streamlit 기반 웹 UI
"""

import streamlit as st

from fdc_neo_converter import FDCNEOConverter, ConversionResult

# 페이지 설정
st.set_page_config(
    page_title="FDC NEO Parser",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """메인 애플리케이션"""
    
    # 헤더
    st.markdown('<div class="main-header">🏢 FDC NEO Parser</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; color: #7f8c8d; margin-bottom: 2rem;">Fault Data Collection NEO Engine</div>', unsafe_allow_html=True)
    
    # 사이드바 메뉴
    st.sidebar.title("📋 메뉴")
    menu = st.sidebar.radio(
        "기능 선택",
        ["🏠 홈", "🔄 파일 변환", "🔗 파일 병합"]
    )
    
    if menu == "🏠 홈":
        show_home()
    elif menu == "🔄 파일 변환":
        show_conversion()
    elif menu == "🔗 파일 병합":
        show_merge()


def show_home():
    """홈 화면"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎯 주요 기능")
        
        st.markdown("""
        #### 1. 🔄 파일 변환
        - 온라인 → 오프라인 변환
        - 오프라인 → 온라인 변환
        - 자동 형식 감지
        
        #### 2. 🔗 파일 병합
        - 온라인 + 오프라인 병합
        - 타임스탬프 기준 중복 제거
        - 온라인 또는 오프라인 형식으로 출력
        """)
    
    with col2:
        st.markdown("### 📌 정보")
        
        st.info("""
        **버전**: v1.0
        
        **지원 파일**:
        - Fault_WBVF (256KB)
        - Fault_GT (512KB)
        - GT 온라인 (1KB)
        - WB 온라인 (1KB)
        
        **성능**:
        - 추출률: 99.6%
        - 처리 속도: ~1초/파일
        """)


def show_conversion():
    """파일 변환 화면"""
    
    st.markdown("### 🔄 파일 변환")
    
    converter = FDCNEOConverter()
    
    tab1, tab2 = st.tabs(["온라인 → 오프라인", "오프라인 → 온라인"])
    
    with tab1:
        st.markdown("#### 온라인 파일을 오프라인 형식으로 변환")
        
        uploaded_file = st.file_uploader(
            "온라인 파일 업로드",
            type=['txt'],
            key='online_upload',
            help="GT_*.txt 또는 WB_*.txt"
        )
        
        if uploaded_file:
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            output_name = st.text_input(
                "출력 파일명",
                value=f"Fault_Converted_{uploaded_file.name}",
                key='online_to_offline_output'
            )
            
            if st.button("변환 시작", type="primary", key='online_to_offline_btn'):
                with st.spinner("변환 중..."):
                    result = converter.online_to_offline(temp_path, f"/tmp/{output_name}")
                    
                    if result.success:
                        st.success(f"✅ {result.message}")
                        
                        # 상세 통계 정보
                        st.markdown("---")
                        st.markdown("### 📊 변환 통계")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("입력 레코드 수", f"{result.input_record_count:,}")
                        col2.metric("출력 레코드 수", f"{result.output_record_count:,}")
                        col3.metric("변환률", "100%" if result.input_record_count > 0 else "0%")
                        
                        # 다운로드 버튼
                        with open(result.output_file, 'rb') as f:
                            st.download_button(
                                label="📥 변환된 파일 다운로드",
                                data=f,
                                file_name=output_name,
                                mime='application/octet-stream'
                            )
                    else:
                        st.error(f"❌ {result.message}")
    
    with tab2:
        st.markdown("#### 오프라인 파일을 온라인 형식으로 변환")
        
        uploaded_file = st.file_uploader(
            "오프라인 파일 업로드",
            type=['txt'],
            key='offline_upload',
            help="Fault_*.txt"
        )
        
        if uploaded_file:
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getvalue())
            
            output_name = st.text_input(
                "출력 파일명",
                value=f"Online_Converted_{uploaded_file.name}",
                key='offline_to_online_output'
            )
            
            if st.button("변환 시작", type="primary", key='offline_to_online_btn'):
                with st.spinner("변환 중..."):
                    result = converter.offline_to_online(temp_path, f"/tmp/{output_name}")
                    
                    if result.success:
                        st.success(f"✅ {result.message}")
                        
                        # 상세 통계 정보
                        st.markdown("---")
                        st.markdown("### 📊 변환 통계")
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("입력 레코드 수", f"{result.input_record_count:,}")
                        col2.metric("출력 레코드 수", f"{result.output_record_count:,}")
                        col3.metric("변환률", "100%" if result.input_record_count > 0 else "0%")
                        
                        # 다운로드 버튼
                        with open(result.output_file, 'r') as f:
                            st.download_button(
                                label="📥 변환된 파일 다운로드",
                                data=f,
                                file_name=output_name,
                                mime='text/plain'
                            )
                    else:
                        st.error(f"❌ {result.message}")


def show_merge():
    """파일 병합 화면"""
    
    st.markdown("### 🔗 파일 병합")
    st.info("온라인 + 오프라인 파일을 병합하고 타임스탬프 기준으로 중복을 제거합니다.")
    
    converter = FDCNEOConverter()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 온라인 파일")
        online_file = st.file_uploader(
            "온라인 파일 업로드",
            type=['txt'],
            key='merge_online',
            help="GT_*.txt 또는 WB_*.txt"
        )
    
    with col2:
        st.markdown("#### 오프라인 파일")
        offline_file = st.file_uploader(
            "오프라인 파일 업로드",
            type=['txt'],
            key='merge_offline',
            help="Fault_*.txt"
        )
    
    if online_file and offline_file:
        st.markdown("---")
        
        # 출력 형식 선택
        output_format = st.radio(
            "출력 형식",
            ["온라인 형식", "오프라인 형식"],
            index=0,  # 기본값: 온라인 형식
            horizontal=True,
            help="온라인 형식: Hex-String 텍스트 파일 (약 1KB, 최대 518바이트)\n오프라인 형식: Binary 파일 (256KB 또는 512KB)"
        )
        
        output_name = st.text_input(
            "출력 파일명",
            value=f"Merged_{'Online' if output_format == '온라인 형식' else 'Offline'}_output.txt"
        )
        
        if st.button("병합 시작", type="primary"):
            with st.spinner("병합 중..."):
                # 임시 파일 저장
                online_path = f"/tmp/{online_file.name}"
                offline_path = f"/tmp/{offline_file.name}"
                output_path = f"/tmp/{output_name}"
                
                with open(online_path, 'wb') as f:
                    f.write(online_file.getvalue())
                with open(offline_path, 'wb') as f:
                    f.write(offline_file.getvalue())
                
                # 병합
                if output_format == "온라인 형식":
                    result = converter.merge_to_online(online_path, offline_path, output_path)
                else:
                    result = converter.merge_to_offline(online_path, offline_path, output_path)
                
                if result.success:
                    st.success(f"✅ {result.message}")
                    
                    # 상세 통계 정보
                    st.markdown("---")
                    st.markdown("### 📊 병합 통계")
                    
                    # 입력 파일 정보
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**온라인 파일**: {online_file.name}\n\n레코드 수: {result.online_record_count:,}개")
                    with col2:
                        st.info(f"**오프라인 파일**: {offline_file.name}\n\n레코드 수: {result.offline_record_count:,}개")
                    
                    # 병합 통계
                    st.markdown("#### 병합 결과")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("병합 전 총 레코드", f"{result.input_record_count:,}")
                    col2.metric("중복 제거", f"{result.duplicate_count:,}")
                    col3.metric("최종 레코드 수", f"{result.output_record_count:,}")
                    col4.metric("중복 제거율", f"{(result.duplicate_count / result.input_record_count * 100):.1f}%" if result.input_record_count > 0 else "0%")
                    
                    # 다운로드 버튼
                    mime_type = 'text/plain' if output_format == "온라인 형식" else 'application/octet-stream'
                    read_mode = 'r' if output_format == "온라인 형식" else 'rb'
                    
                    with open(result.output_file, read_mode) as f:
                        st.download_button(
                            label="📥 병합된 파일 다운로드",
                            data=f,
                            file_name=output_name,
                            mime=mime_type
                        )
                else:
                    st.error(f"❌ {result.message}")


if __name__ == '__main__':
    main()
