import time
import json
import time
import os


def read_3x3_matrix(name):
    """
    Reads a 3x3 matrix from standard input.
    Includes validation to ensure exactly 3 rows and 3 columns of numbers are provided.
    """
    while True:
        print(f"{name} (3줄 입력, 공백 구분)")
        matrix = []
        try:
            for _ in range(3):
                line = input().strip()
                # Convert the space-separated string into a list of floats
                row = [float(x) for x in line.split()]
                
                if len(row) != 3:
                    raise ValueError("행의 요소 개수가 3개가 아닙니다.")
                
                matrix.append(row)
            
            return matrix
            
        except ValueError:
            # If parsing fails or the length is wrong, prompt again
            print("입력 형식 오류: 각 줄에 3개의 숫자를 공백으로 구분해 입력하세요. 다시 입력해주세요.\n")


def mode_1_user_input():
    """
    Executes Mode 1: User Console Input
    """
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#----------------------------------------")
    filter_a = read_3x3_matrix("필터 A")
    print()
    filter_b = read_3x3_matrix("필터 B")
    
    print("\n#----------------------------------------")
    print("# [2] 패턴 입력")
    print("#----------------------------------------")
    pattern = read_3x3_matrix("패턴")
    
    print("\n#----------------------------------------")
    print("# [3] MAC 결과")
    print("#----------------------------------------")
    
    # 1. Calculate actual scores
    score_a = calculate_mac(pattern, filter_a)
    score_b = calculate_mac(pattern, filter_b)
    
    # 2. Performance Analysis: Measure purely the math execution time (10 loops)
    repeats = 10
    start_time = time.perf_counter()
    for _ in range(repeats):
        # We run the function repeatedly just to measure the time
        _ = calculate_mac(pattern, filter_a)
    end_time = time.perf_counter()
    
    # Convert seconds to milliseconds and calculate average
    avg_time_ms = ((end_time - start_time) * 1000) / repeats
    
    # 3. Print Results
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{repeats}회): {avg_time_ms:.3f} ms")
    
    # 4. Make a decision using our Epsilon policy
    if are_scores_tied(score_a, score_b):
        print("판정: 판정 불가 (|A-B| < 1e-9)")
    elif score_a > score_b:
        print("판정: A")
    else:
        print("판정: B")



def mode_2_json_analysis():
    """
    Executes Mode 2: JSON Analysis
    """
    json_path = 'data.json'
    
    if not os.path.exists(json_path):
        print(f"오류: {json_path} 파일을 찾을 수 없습니다.")
        return

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    filters = data.get("filters", {})
    patterns = data.get("patterns", {})

    # Print loaded filters
    for f_key in filters.keys():
        print(f"✓ {f_key} 필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    fail_reasons = []

    # Dictionary to store performance metrics: { size_n: {'time': total_time, 'count': num_measurements} }
    performance_data = {}

    for p_key, p_data in patterns.items():
        print(f"--- {p_key} ---")
        total_tests += 1
        
        # Parse size from key (e.g., "size_5_1" -> "size_5", N = 5)
        parts = p_key.split('_')
        if len(parts) >= 2:
            size_key = f"size_{parts[1]}"
            try:
                n = int(parts[1])
            except ValueError:
                print(f"FAIL: 키 이름({p_key})에서 크기를 추출할 수 없습니다.")
                failed_tests += 1
                fail_reasons.append(f"{p_key}: 키 파싱 실패")
                continue
        else:
            print(f"FAIL: 잘못된 패턴 키 형식 ({p_key})")
            failed_tests += 1
            fail_reasons.append(f"{p_key}: 키 형식 오류")
            continue

        # Validation: Check if the corresponding filter exists
        if size_key not in filters:
            print(f"FAIL: {size_key}에 대한 필터가 존재하지 않습니다.")
            failed_tests += 1
            fail_reasons.append(f"{p_key}: 필터 누락")
            continue

        pattern_matrix = p_data["input"]
        expected_raw = p_data["expected"]
        expected_normalized = normalize_label(expected_raw)

        # Validation: Check pattern dimension matches N x N
        if len(pattern_matrix) != n or any(len(row) != n for row in pattern_matrix):
            print(f"FAIL: 패턴 크기 불일치 (예상: {n}x{n})")
            failed_tests += 1
            fail_reasons.append(f"{p_key}: 크기 불일치")
            continue

        # Get filters and normalize their keys (assuming 'cross' and 'x' are in the JSON)
        filter_cross = None
        filter_x = None
        for raw_f_key, f_matrix in filters[size_key].items():
            norm_f_key = normalize_label(raw_f_key)
            if norm_f_key == 'Cross':
                filter_cross = f_matrix
            elif norm_f_key == 'X':
                filter_x = f_matrix

        if not filter_cross or not filter_x:
            print(f"FAIL: {size_key}에 유효한 Cross/X 필터가 부족합니다.")
            failed_tests += 1
            fail_reasons.append(f"{p_key}: 표준 필터 누락")
            continue

        # Calculate Scores & Measure Time
        repeats = 10
        start_time = time.perf_counter()
        
        for _ in range(repeats):
            # Run MAC operations
            score_cross = calculate_mac(pattern_matrix, filter_cross)
            score_x = calculate_mac(pattern_matrix, filter_x)
            
        end_time = time.perf_counter()
        
        # Save time for performance table (record time for a single MAC operation pair, scaled later)
        avg_time_ms = ((end_time - start_time) * 1000) / repeats
        if n not in performance_data:
            performance_data[n] = []
        performance_data[n].append(avg_time_ms)

        print(f"Cross 점수: {score_cross}")
        print(f"X 점수: {score_x}")

        # Decide based on Epsilon
        decision = "UNDECIDED"
        if are_scores_tied(score_cross, score_x):
            decision = "UNDECIDED"
        elif score_cross > score_x:
            decision = "Cross"
        else:
            decision = "X"

        # Check PASS/FAIL
        if decision == expected_normalized:
            print(f"판정: {decision} | expected: {expected_normalized} | PASS")
            passed_tests += 1
        else:
            fail_msg = f"동점(UNDECIDED) 처리 규칙에 따라 FAIL" if decision == "UNDECIDED" else f"점수 비교 실패"
            print(f"판정: {decision} | expected: {expected_normalized} | FAIL ({fail_msg})")
            failed_tests += 1
            fail_reasons.append(f"{p_key}: {fail_msg} (판정: {decision}, 예상: {expected_normalized})")

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수(N²)'}")
    print("-" * 45)
    
    # Sort sizes for the output table
    for n in sorted(performance_data.keys()):
        # Average the times if there were multiple patterns of the same size
        overall_avg_ms = sum(performance_data[n]) / len(performance_data[n])
        operations = n * n
        print(f"{n}x{n:<8} {overall_avg_ms:<15.3f} {operations}")

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    print(f"총 테스트: {total_tests}개")
    print(f"통과: {passed_tests}개")
    print(f"실패: {failed_tests}개")

    if failed_tests > 0:
        print("\n실패 케이스:")
        for reason in fail_reasons:
            print(f"- {reason}")
        print("(상세 원인 분석 및 복잡도 설명은 README.md의 '결과 리포트' 섹션에 작성)")
    else:
        print("\n모든 케이스를 통과했습니다!")



def calculate_mac(pattern, filter_matrix):
    """
    Performs a Multiply-Accumulate (MAC) operation on two 2D arrays of the same size.
    """
    score = 0.0
    n = len(pattern)
    
    # Iterate through rows and columns to multiply corresponding elements
    for i in range(n):
        for j in range(n):
            score += pattern[i][j] * filter_matrix[i][j]
            
    return score


def normalize_label(raw_label):
    """
    Converts various input strings into standard labels: 'Cross' or 'X'.
    """
    label_lower = str(raw_label).strip().lower()
    
    if label_lower in ['+', 'cross']:
        return 'Cross'
    elif label_lower in ['x']:
        return 'X'
    
    return 'UNDECIDED'


def are_scores_tied(score_a, score_b, epsilon=1e-9):
    """
    Checks if two floating-point scores are close enough to be considered a tie.
    """
    return abs(score_a - score_b) < epsilon


if __name__ == "__main__":
    print("=== Mini NPU Simulator ===")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    
    choice = input("선택: ").strip()
    
    if choice == '1':
        mode_1_user_input()
    elif choice == '2':
        mode_2_json_analysis()
    else:
        print("잘못된 입력입니다. 프로그램을 종료합니다.")