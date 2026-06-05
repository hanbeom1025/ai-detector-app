import streamlit as st
import google.generativeai as genai
from PIL import Image
import cv2
import tempfile
import os  # 🔴 1. os 모듈 임포트 추가

# 1. 페이지 및 세션 초기화
st.set_page_config(page_title="AI 생성물 판별 및 학습 앱", layout="centered")

# 퀴즈 진행도 관련 세션 상태 초기화
if 'quiz_idx' not in st.session_state:
    st.session_state.quiz_idx = 0
    st.session_state.quiz_score = 0
    st.session_state.show_answer = False

# ==========================================
# 🔴 구글 Gemini API 키 설정 및 모델 초기화
# ==========================================
GEMINI_API_KEY = "AQ.Ab8RN6L7CCAGJ3z780V8VnNhSpRc4vbbEb08nzKLblgUqAPh-A"
genai.configure(api_key=GEMINI_API_KEY)

# 텍스트 및 이미지 분석용 모델
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# ==========================================
# 📂 [코드에서 직접 관리하는 이미지 가이드라인]
# ==========================================
IMAGE_GUIDELINES = [
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.1.png",
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.2.png",
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.3.png",
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.4.png",
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.5.png",
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.6.png",
    r"C:\Users\LG\OneDrive\Desktop\images\AI 생성물 판별 가이드라인 p.7.png"
]

# --- Gemini API 분석 함수 ---
def analyze_with_gemini(data, data_type):
    try:
        guideline_hints = ", ".join([os.path.basename(p) for p in IMAGE_GUIDELINES])
        
        if data_type == "text":
            prompt = f"""
            당신은 AI 생성물 판별 전문가입니다. 다음 텍스트가 AI에 의해 작성되었을 확률을 분석하세요.
            반드시 아래 두 줄 형식으로만 답변하세요.
            확률: [0~100 숫자]
            근거: [1~2문장 설명]
            
            텍스트: {data}
            """
            response = model.generate_content(prompt)
            
        elif data_type == "image":
            prompt = f"""
            당신은 딥페이크 및 AI 생성 이미지 판별 전문가입니다.
            제공된 이미지에 AI 합성 흔적(손가락 기형, 배경 글자 뭉개짐, 부자연스러운 그림자/눈 표현 등)이 있는지 확인하세요.
            반드시 아래 두 줄 형식으로만 답변하세요.
            확률: [0~100 숫자]
            근거: [1~2문장 설명]
            """
            response = model.generate_content([prompt, data])

        result_text = response.text.strip()
        lines = [line.strip() for line in result_text.split('\n') if line.strip()]
        
        # 안전한 파싱을 위한 예외 처리 강화
        score = 50
        reason = "근거 추출 실패"
        
        for line in lines:
            if "확률" in line:
                score_str = ''.join(filter(str.isdigit, line))
                if score_str:
                    score = int(score_str)
            elif "근거" in line:
                reason = line.replace('근거:', '').strip()
        
        if len(lines) >= 2 and reason == "근거 추출 실패":
            reason = lines[1]

        return {"score": score / 100.0, "reason": reason}
        
    except Exception as e:
        return {"error": f"API 에러: {str(e)}"}

def display_result(result):
    if "error" in result:
        st.error(result["error"])
        return
    score = result['score']
    percentage = int(score * 100)
    is_ai = percentage >= 50
    
    bg_color = "#f8d7da" if is_ai else "#d4edda"
    text_color = "#721c24" if is_ai else "#155724"
    status_text = "⚠️ AI 생성 가능성 높음" if is_ai else "✅ 실제(인간) 데이터 가능성 높음"

    st.markdown(f"""
    <div style="background-color:{bg_color}; padding: 15px; border-radius: 5px; color:{text_color}; text-align:center;">
        <h4>판별 결과: {'FAKE (AI)' if is_ai else 'REAL'}</h4>
        <h2>확률: {percentage}%</h2>
        <p><strong>{status_text}</strong></p>
        <hr style="opacity: 0.3;">
        <p style="font-size: 0.9em;"><strong>근거:</strong> {result['reason']}</p>
    </div>
    """, unsafe_allow_html=True)
    st.progress(score)

# ==========================================
# 사이드바 네비게이션
# ==========================================
with st.sidebar:
    st.title("메뉴")
    menu = st.radio("이동할 페이지를 선택하세요:", ["🔍 AI 판별기", "🖼️ 판별 가이드라인 보기", "🎯 AI 판별 퀴즈"])
    
    st.divider()
    st.subheader("💡 가이드라인")
    st.write(f"총 {len(IMAGE_GUIDELINES)}개의 참조 이미지가 등록되어 있습니다.")

# ==========================================
# 메인 화면 라우팅
# ==========================================

# --- 1. AI 판별기 ---
if menu == "🔍 AI 판별기":
    st.title("🤖 AI 생성물 판별기")
    st.write("등록된 시각 자료 지표를 기반으로 AI가 생성 여부를 분석합니다.")
    
    tab1, tab2, tab3 = st.tabs(["📝 텍스트", "🖼️ 이미지", "🎥 영상"])
    
    with tab1:
        user_text = st.text_area("텍스트 입력:", height=150)
        if st.button("텍스트 판별", type="primary"):
            if user_text:
                with st.spinner("분석 중..."):
                    display_result(analyze_with_gemini(user_text, "text"))
                    
    with tab2:
        uploaded_image = st.file_uploader("이미지 업로드", type=["png", "jpg", "jpeg"])
        if uploaded_image:
            image = Image.open(uploaded_image).convert("RGB")
            st.image(image, use_container_width=True)
            if st.button("이미지 판별", type="primary"):
                with st.spinner("분석 중..."):
                    display_result(analyze_with_gemini(image, "image"))
                    
    with tab3:
        uploaded_video = st.file_uploader("영상 업로드 (최대 10MB)", type=["mp4", "mov"])
        if uploaded_video:
            st.video(uploaded_video)
            if st.button("영상 판별", type="primary"):
                with st.spinner("중간 프레임 추출 및 분석 중..."):
                    tfile = tempfile.NamedTemporaryFile(delete=False) 
                    tfile.write(uploaded_video.read())
                    tfile.close() # 🔴 2. Windows 환경에서 파일 잠김 방지를 위해 먼저 닫기
                    
                    vidcap = cv2.VideoCapture(tfile.name)
                    vidcap.set(cv2.CAP_PROP_POS_FRAMES, int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT)) // 2)
                    success, frame = vidcap.read()
                    vidcap.release()
                    
                    try:
                        os.unlink(tfile.name) # 사용 임시 파일 삭제
                    except:
                        pass
                        
                    if success:
                        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                        display_result(analyze_with_gemini(pil_img, "image"))
                    else:
                        st.error("프레임 추출 실패. 영상 파일 포맷을 확인해 주세요.")

# --- 2. 가이드라인 보기 (글 없이 이미지만 표기) ---
elif menu == "🖼️ 판별 가이드라인 보기":
    st.title("🖼️ AI 생성물 판별 가이드라인")
    st.write("AI가 만들어낸 흔적들을 담은 예시 사진들입니다. 사진을 보며 인공적인 패턴을 익혀보세요.")
    st.divider()
    
    for idx, img_path in enumerate(IMAGE_GUIDELINES):
        st.subheader(f"📷 참고 예시 {idx+1}")
        try:
            st.image(img_path, use_container_width=True)
        except Exception:
            st.error(f"이미지를 불러올 수 없습니다. 경로를 확인해 주세요: {img_path}")
        st.divider()

# --- 3. AI 판별 퀴즈 ---
elif menu == "🎯 AI 판별 퀴즈":
    st.title("🎯 AI 생성물 구별 퀴즈")
    st.write("가이드라인을 바탕으로 직접 AI 생성물을 찾아보세요!")
    
    quiz_data = [
        {
            "type": "text", 
            "content": "이 혁신적인 솔루션은 전례 없는 효율성을 제공하며, 다양한 산업 분야에서 패러다임의 전환을 이끌어 낼 것입니다.", 
            "answer": "AI", 
            "reason": "전형적인 챗봇 특유의 과장된 어휘(혁신적인, 전례 없는, 패러다임 전환)가 사용된 기계적 문장입니다."
        },
        {
            "type": "text",
            "content": "오늘 점심에 짬뽕 먹었는데 국물이 진짜 끝내주더라ㅋㅋ 너도 나중에 꼭 가봐 진심 강추",
            "answer": "Human",
            "reason": "자연스러운 구어체와 감정 표현이 담긴 인간의 문장입니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진1.jpg", 
            "answer": "Human", 
            "reason": "인물들의 표정이 매우 현실적이며, 옷의 글자들이 정확합니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진2.jpg", 
            "answer": "AI", 
            "reason": "그림자가 매우 부자연스럽습니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진4.jpg", 
            "answer": "AI", 
            "reason": "사진 속 요소가 지나치게 선명하다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진5.jpg", 
            "answer": "Human", 
            "reason": "햇빛의 경로들이 매우 자연스럽습니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진6.jpg", 
            "answer": "AI", 
            "reason": "ppt의 사진이 일그러져 있습니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진7.jpg", 
            "answer": "Human", 
            "reason": "우비의 움직임과 빗물의 표현이 자연스럽습니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진8.jpg", 
            "answer": "AI", 
            "reason": "간판의 글자들이 일그러져 있습니다. "
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진9.jpg", 
            "answer": "AI", 
            "reason": "눈이 내리는 표현이 부자연스럽습니다."
        },
        {
            "type": "image", 
            "content": r"C:\Users\LG\OneDrive\Desktop\images\사진10.jpg", 
            "answer": "Human", 
            "reason": "구름의 표현이 현실과 매우 유사합니다."
        }
    ]
    
    total_q = len(quiz_data)
    idx = st.session_state.quiz_idx
    
    if idx < total_q:
        st.subheader(f"문제 {idx + 1} / {total_q}")
        st.progress((idx) / total_q)
        
        current_q = quiz_data[idx]
        
        st.markdown("""<div style="padding: 20px; border: 2px solid #ddd; border-radius: 10px; margin-bottom: 20px;">""", unsafe_allow_html=True)
        if current_q["type"] == "text":
            st.write(current_q["content"])
        elif current_q["type"] == "image":
            try:
                st.image(current_q["content"], use_container_width=True)
            except:
                st.error("이미지 파일을 찾을 수 없습니다. 경로를 확인하세요.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if not st.session_state.show_answer:
            st.write("이것은 누가 만든 것일까요?")
            col1, col2 = st.columns(2)
            if col1.button("🤖 AI가 생성했다", use_container_width=True):
                st.session_state.user_choice = "AI"
                st.session_state.show_answer = True
                st.rerun()
            if col2.button("🙋 사람이 만들었다", use_container_width=True):
                st.session_state.user_choice = "Human"
                st.session_state.show_answer = True
                st.rerun()
        else:
            is_correct = st.session_state.user_choice == current_q["answer"]
            if is_correct:
                st.success("🎉 정답입니다!")
            else:
                st.error("❌ 오답입니다.")
                
            st.info(f"**해설:** {current_q['reason']}")
            
            if st.button("다음 문제로", type="primary"):
                if is_correct:
                    st.session_state.quiz_score += 1
                st.session_state.quiz_idx += 1
                st.session_state.show_answer = False
                st.rerun()
    else:
        st.balloons()
        st.subheader("퀴즈 종료!")
        st.write(f"최종 점수: {total_q}문제 중 {st.session_state.quiz_score}문제 정답")
        
        if st.button("퀴즈 다시 풀기"):
            st.session_state.quiz_idx = 0
            st.session_state.quiz_score = 0
            st.session_state.show_answer = False
            st.rerun()