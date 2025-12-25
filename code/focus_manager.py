import time

# =============================================================================
# 1. CẤU HÌNH HẰNG SỐ (ĐÃ CẬP NHẬT CHU KỲ PHẠT)
# =============================================================================

# --- Thời gian & Điểm ---
HAND_RAISE_COOLDOWN = 30.0       # Giây giữa 2 lần cộng điểm giơ tay
GOOD_FOCUS_TARGET_TIME = 300.0   # 5 phút tập trung -> +1 điểm
GOOD_FOCUS_POINTS = 1

PHONE_REPEAT_PENALTY_TIME = 180.0 # [FIX] Đúng 3 phút (180s) mới trừ tiếp 1 điểm
PHONE_POINTS = -1

HEAD_TURN_FIRST_PENALTY_TIME = 60.0 
HEAD_TURN_REPEAT_PENALTY_TIME = 120.0 
HEAD_TURN_POINTS = -1

SLEEPY_EYES_TRIGGER_TIME = 60.0   
SLEEP_FIRST_PENALTY_TIME = 180.0  
SLEEP_REPEAT_PENALTY_TIME = 180.0 
SLEEP_POINTS = -1

MAX_FRAME_INTERVAL = 1.5 # Ngưỡng chặn lỗi lag/nhảy ID

# --- Danh sách hành vi ---
ALL_BEHAVIOR_NAMES = [
    'reading', 'writing', 'upright',
    'hand-raising',
    'Using_phone', 'phone', 
    'sleep', 'bend',
    'HEAD_LEFT', 'HEAD_RIGHT',
    'EYES_CLOSING', 
    'head_tilt_left', 'head_tilt_right',
    'EYES_OPEN', 'HEAD_STRAIGHT'
]

GOOD_BEHAVIORS = {'reading', 'writing', 'upright'}
BAD_BEHAVIORS_FOR_RESET = {'Using_phone', 'phone', 'sleep', 'bend'}


# =============================================================================
# 2. CLASS QUẢN LÝ ĐIỂM (LOGIC ĐÃ FIX LỖI TRỪ ĐIỂM ĐIỆN THOẠI)
# =============================================================================

class FocusScoreManager:
    def __init__(self, base_score=10):
        self.students = {}
        self.base_score = base_score
        self.ALL_BEHAVIORS = ALL_BEHAVIOR_NAMES
        self.GOOD_BEHAVIORS = GOOD_BEHAVIORS
        self.BAD_BEHAVIORS_FOR_RESET = BAD_BEHAVIORS_FOR_RESET

    def _get_student_state(self, student_id):
        if student_id not in self.students:
            current_time = time.time() 
            new_state = {
                'score': self.base_score,
                'last_update_time': current_time, 
                
                # --- Timer cho Quy tắc CỘNG điểm ---
                'last_hand_raise_time': 0.0,
                'is_currently_raising_hand': False,
                'good_focus_cumulative_time': 0.0,
                
                # --- Timer cho Quy tắc TRỪ điểm ---
                'last_phone_penalty_time': 0.0,      # Lưu mốc thời gian bị phạt điện thoại gần nhất
                'head_turn_start_time': 0.0,
                'last_head_turn_penalty_time': 0.0,
                'sleepy_eyes_start_time': 0.0,
                'sleep_pose_start_time': 0.0,
                'last_sleep_penalty_time': 0.0,
                
                'session_logs': [] 
            }
            for behavior_name in self.ALL_BEHAVIORS:
                new_state[f"{behavior_name}_timer_session"] = 0.0
            self.students[student_id] = new_state
        return self.students[student_id]

    def update_student_score(self, student_id, behaviors_list, head_state, eye_state, current_time=None):
        if current_time is None:
            current_time = time.time()
            
        state = self._get_student_state(student_id)
        new_points = 0
        log_tuples = []

        # --- BƯỚC 1: XỬ LÝ DELTA TIME & LAG ---
        delta_time = 0
        if state['last_update_time'] > 0:
            delta_time = current_time - state['last_update_time']
        if delta_time > MAX_FRAME_INTERVAL:
            delta_time = 0 
        state['last_update_time'] = current_time

        # --- BƯỚC 2: XÁC ĐỊNH TRẠNG THÁI ---
        behavior_labels = set(behaviors_list)
        if head_state != 'NO_FACE': behavior_labels.add(head_state)
        if eye_state != 'NO_FACE': behavior_labels.add(eye_state)

        is_good_focus = any(b in behavior_labels for b in self.GOOD_BEHAVIORS)
        is_phone = any(b in behavior_labels for b in ['Using_phone', 'phone'])
        is_head_turn = (head_state in ['HEAD_LEFT', 'HEAD_RIGHT'])
        
        # Xử lý ngủ (nhắm mắt lâu hoặc cúi gục)
        if eye_state == 'EYES_CLOSING':
            if state['sleepy_eyes_start_time'] == 0: state['sleepy_eyes_start_time'] = current_time
            is_confirmed_sleepy = (current_time - state['sleepy_eyes_start_time'] > SLEEPY_EYES_TRIGGER_TIME)
        else:
            state['sleepy_eyes_start_time'] = 0
            is_confirmed_sleepy = False
            
        is_sleep_pose = any(b in behavior_labels for b in ['sleep', 'bend']) or is_confirmed_sleepy
        is_bad_event_for_reset = bool(behavior_labels.intersection(self.BAD_BEHAVIORS_FOR_RESET))

        # --- BƯỚC 3: CẬP NHẬT TIMERS THỐNG KÊ ---
        for behavior_name in self.ALL_BEHAVIORS:
            if behavior_name in behavior_labels:
                state[f"{behavior_name}_timer_session"] += delta_time

        # --- BƯỚC 4: QUY TẮC TẬP TRUNG 5 PHÚT ---
        if is_bad_event_for_reset:
            if state['good_focus_cumulative_time'] > 0:
                log_tuples.append((current_time, "Mất chuỗi tập trung (làm việc riêng)", 0))
            state['good_focus_cumulative_time'] = 0.0
        elif is_good_focus:
            state['good_focus_cumulative_time'] += delta_time
            if state['good_focus_cumulative_time'] >= GOOD_FOCUS_TARGET_TIME:
                new_points += GOOD_FOCUS_POINTS
                log_tuples.append((current_time, f"+{GOOD_FOCUS_POINTS} (Đủ 5p tập trung)", GOOD_FOCUS_POINTS))
                state['good_focus_cumulative_time'] = 0.0

        # --- BƯỚC 5: GIƠ TAY ---
        if 'hand-raising' in behavior_labels:
            if not state['is_currently_raising_hand']:
                if current_time - state['last_hand_raise_time'] > HAND_RAISE_COOLDOWN:
                    new_points += 1
                    log_tuples.append((current_time, "+1 (Phát biểu)", 1))
                    state['last_hand_raise_time'] = current_time
                state['is_currently_raising_hand'] = True
        else:
            state['is_currently_raising_hand'] = False

        # --- BƯỚC 6: XỬ LÝ TRỪ ĐIỂM (PENALTIES) ---

        # 6.1. Dùng điện thoại (FIXED LOGIC)
        if is_phone:
            # Nếu là lần đầu phát hiện HOẶC đã trôi qua 3 phút kể từ lần phạt cuối
            time_since_last = current_time - state['last_phone_penalty_time']
            
            if state['last_phone_penalty_time'] == 0 or time_since_last >= PHONE_REPEAT_PENALTY_TIME:
                new_points += PHONE_POINTS
                state['last_phone_penalty_time'] = current_time
                
                label = "Bắt đầu dùng điện thoại" if time_since_last > 1000 else "Vẫn dùng điện thoại > 3p"
                log_tuples.append((current_time, f"{PHONE_POINTS} ({label})", PHONE_POINTS))
        # Lưu ý: Không reset last_phone_penalty_time về 0 khi không thấy điện thoại 
        # để giữ vững chu kỳ 3 phút dù AI bị mất dấu tạm thời.

        # 6.2. Quay đầu
        if is_head_turn:
            if state['head_turn_start_time'] == 0:
                state['head_turn_start_time'] = current_time
                state['last_head_turn_penalty_time'] = current_time
            else:
                duration = current_time - state['head_turn_start_time']
                since_penalty = current_time - state['last_head_turn_penalty_time']
                
                if duration > HEAD_TURN_FIRST_PENALTY_TIME and state['last_head_turn_penalty_time'] == state['head_turn_start_time']:
                    new_points += HEAD_TURN_POINTS
                    log_tuples.append((current_time, f"{HEAD_TURN_POINTS} (Quay đầu >1p)", HEAD_TURN_POINTS))
                    state['last_head_turn_penalty_time'] = current_time
                elif since_penalty > HEAD_TURN_REPEAT_PENALTY_TIME:
                    new_points += HEAD_TURN_POINTS
                    log_tuples.append((current_time, f"{HEAD_TURN_POINTS} (Vẫn quay đầu >2p)", HEAD_TURN_POINTS))
                    state['last_head_turn_penalty_time'] = current_time
        else:
            state['head_turn_start_time'] = 0

        # 6.3. Ngủ
        if is_sleep_pose:
            if state['sleep_pose_start_time'] == 0:
                state['sleep_pose_start_time'] = current_time
                state['last_sleep_penalty_time'] = current_time
            else:
                duration = current_time - state['sleep_pose_start_time']
                since_penalty = current_time - state['last_sleep_penalty_time']
                
                if duration > SLEEP_FIRST_PENALTY_TIME and state['last_sleep_penalty_time'] == state['sleep_pose_start_time']:
                    new_points += SLEEP_POINTS
                    log_tuples.append((current_time, f"{SLEEP_POINTS} (Ngủ gật >3p)", SLEEP_POINTS))
                    state['last_sleep_penalty_time'] = current_time
                elif since_penalty > SLEEP_REPEAT_PENALTY_TIME:
                    new_points += SLEEP_POINTS
                    log_tuples.append((current_time, f"{SLEEP_POINTS} (Vẫn ngủ >3p)", SLEEP_POINTS))
                    state['last_sleep_penalty_time'] = current_time
        else:
            state['sleep_pose_start_time'] = 0

        # --- BƯỚC 7: KẾT THÚC ---
        if new_points != 0:
            state['score'] += new_points
        if log_tuples:
            state['session_logs'].extend(log_tuples)
            
        return new_points, [msg for ts, msg, change in log_tuples]

    # --- Các hàm bổ trợ UI ---
    def get_student_score(self, student_id):
        return self.students.get(student_id, {}).get('score', self.base_score)

    def get_student_timers(self, student_id):
        st = self.students.get(student_id, {})
        timers = {b: st.get(f"{b}_timer_session", 0.0) for b in self.ALL_BEHAVIORS}
        timers['good_focus'] = st.get('good_focus_cumulative_time', 0.0)
        return timers
    def get_student_full_logs(self, student_id):
        """
        Lấy toàn bộ danh sách log (timestamp, message, point) của một học sinh.
        """
        state = self._get_student_state(student_id)
        return state.get('session_logs', [])

    def get_student_score(self, student_id):
        state = self._get_student_state(student_id)
        return state.get('score', self.base_score)

    def get_student_timers(self, student_id):
        st = self.students.get(student_id, {})
        timers = {b: st.get(f"{b}_timer_session", 0.0) for b in self.ALL_BEHAVIORS}
        timers['good_focus'] = st.get('good_focus_cumulative_time', 0.0)
        return timers