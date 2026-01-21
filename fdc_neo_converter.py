#!/usr/bin/env python3
"""
FDC NEO Converter
온라인 ↔ 오프라인 파일 변환 및 병합
"""

import os
from datetime import datetime
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConversionResult:
    """변환 결과"""
    success: bool
    output_file: str
    record_count: int
    message: str
    # 통계 정보 (선택적)
    input_record_count: int = 0  # 입력 파일 레코드 수
    output_record_count: int = 0  # 출력 파일 레코드 수
    duplicate_count: int = 0  # 중복 제거된 레코드 수 (병합 시)
    online_record_count: int = 0  # 온라인 파일 레코드 수 (병합 시)
    offline_record_count: int = 0  # 오프라인 파일 레코드 수 (병합 시)


class FDCNEOConverter:
    """FDC NEO 파일 변환기"""
    
    def __init__(self):
        self.records = []
    
    # =====================================================================
    # 1. 온라인 → 오프라인 변환
    # =====================================================================
    
    def online_to_offline(self, online_file: str, output_file: str = None) -> ConversionResult:
        """
        온라인 파일을 오프라인 형식으로 변환
        
        Args:
            online_file: 온라인 파일 경로 (GT_*.txt, WB_*.txt)
            output_file: 출력 파일 경로 (없으면 자동 생성)
        
        Returns:
            ConversionResult
        """
        try:
            # 1. 온라인 파일 읽기 (Hex-String)
            with open(online_file, 'rb') as f:
                hex_string = f.read().decode('ascii').strip()
            
            # 2. Binary로 변환
            binary_data = bytes.fromhex(hex_string)
            
            # 3. 온라인 파일에서 레코드 데이터만 추출 (파일 타임스탬프와 헤더 제거)
            # 온라인 형식: [파일타임스탬프 6B][헤더 2B][레코드 데이터...]
            if len(binary_data) > 8:
                record_data = binary_data[8:]  # 파일 타임스탬프(6) + 헤더(2) 제거
            else:
                record_data = binary_data
            
            # 4. 출력 파일명 생성
            if output_file is None:
                base_name = os.path.basename(online_file)
                # GT_N24987L02_260107_091837.txt → Fault_GT_N24987L02.txt
                if base_name.startswith('GT_'):
                    parts = base_name.split('_')
                    output_file = f"Fault_GT_{parts[1]}.txt"
                elif base_name.startswith('WB_'):
                    parts = base_name.split('_')
                    output_file = f"Fault_WBVF_{parts[1]}.txt"
                else:
                    output_file = "Fault_Converted.txt"
            
            # 5. 오프라인 형식 생성
            offline_data = self._create_offline_format(record_data, is_gt='GT_' in online_file)
            
            # 6. 파일 저장
            with open(output_file, 'wb') as f:
                f.write(offline_data)
            
            # 7. 레코드 수 계산
            input_record_count = record_data.count(b'\x07\xE9') + record_data.count(b'\x07\xEA') + \
                                record_data.count(b'\x07\xEB') + record_data.count(b'\x07\xE7')
            output_record_count = input_record_count  # 변환 시 레코드 수는 동일
            
            return ConversionResult(
                success=True,
                output_file=output_file,
                record_count=output_record_count,
                message=f"온라인 → 오프라인 변환 성공: {output_record_count}개 레코드",
                input_record_count=input_record_count,
                output_record_count=output_record_count
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output_file="",
                record_count=0,
                message=f"변환 실패: {str(e)}"
            )
    
    def _create_offline_format(self, record_data: bytes, is_gt: bool = True) -> bytes:
        """오프라인 파일 형식 생성
        
        구조 (문서 기준):
        - ConfigDone 헤더: 오프셋 0-9 (10 bytes)
        - 설정 데이터: 오프셋 10-41 (32 bytes)
        - 시스템 식별자: 오프셋 42-45 (WBVF 4B) 또는 42-44 (GSP 3B)
        - 설정 데이터 계속: 오프셋 46-272 (227 bytes for WBVF, 228 bytes for GT)
        - 인덱스 테이블: 오프셋 273-472 (200 bytes)
        - 레코드 데이터: 오프셋 ~7000 이후부터 시작
        """
        
        # ConfigDone 헤더 (10 bytes)
        config_done = b'ConfigDone'
        
        # 설정 데이터 영역 (32 bytes, 오프셋 10-41)
        config_area_1 = b'\x00' * 32
        
        # 시스템 식별자 (오프셋 42부터)
        if is_gt:
            identifier = b'GSP'  # 3 bytes
            config_area_2 = b'\x00' * 228  # 오프셋 45-272 (228 bytes)
        else:
            identifier = b'WBVF'  # 4 bytes
            config_area_2 = b'\x00' * 227  # 오프셋 46-272 (227 bytes)
        
        # 인덱스 테이블 (200 bytes, 오프셋 273-472)
        # B2, B1, 1, 2, 3, ... 형식
        index_table = b'\x00\x00' + b'B2\x00B1\x00' + b'1\x00\x002\x00\x003\x00\x00'
        # 나머지 인덱스 항목들 (간단한 버전)
        index_table += b'\x00' * (200 - len(index_table))
        
        # 레코드 데이터 시작 위치까지 패딩 (~7000 오프셋)
        # 현재까지: 10 + 32 + (3 or 4) + (228 or 227) + 200 = 473 or 474 bytes
        # 레코드 시작 위치까지: 7000 - 473 = 6527 bytes (GT 기준)
        record_start_padding = b'\x00' * (7000 - len(config_done) - len(config_area_1) - len(identifier) - len(config_area_2) - len(index_table))
        
        # 전체 구조
        offline_data = config_done + config_area_1 + identifier + config_area_2 + index_table + record_start_padding + record_data
        
        # 256KB 또는 512KB로 패딩
        target_size = 524288 if is_gt else 262144  # 512KB or 256KB
        if len(offline_data) < target_size:
            offline_data += b'\x00' * (target_size - len(offline_data))
        else:
            offline_data = offline_data[:target_size]
        
        return offline_data
    
    # =====================================================================
    # 2. 오프라인 → 온라인 변환
    # =====================================================================
    
    def offline_to_online(self, offline_file: str, output_file: str = None) -> ConversionResult:
        """
        오프라인 파일을 온라인 형식으로 변환 (전체 데이터 포함)
        
        Args:
            offline_file: 오프라인 파일 경로 (Fault_*.txt)
            output_file: 출력 파일 경로 (없으면 자동 생성)
        
        Returns:
            ConversionResult
        """
        try:
            # 1. 오프라인 파일에서 레코드 추출
            records = self._extract_records_from_offline(offline_file)
            
            # 타임스탬프 기준 정렬 (최신순, None 타임스탬프는 가장 오래된 것으로 처리)
            records.sort(key=lambda r: r[0] if r[0] is not None else datetime.min, reverse=True)
            
            if not records:
                return ConversionResult(
                    success=False,
                    output_file="",
                    record_count=0,
                    message="추출 가능한 레코드가 없습니다"
                )
            
            # 2. 출력 파일명 생성 (FULL 표시)
            if output_file is None:
                base_name = os.path.basename(offline_file)
                timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
                
                if 'WBVF' in base_name:
                    parts = base_name.split('_')
                    site_id = parts[2].replace('.txt', '')
                    output_file = f"WB_FULL_{site_id}_{timestamp}.txt"
                elif 'GT' in base_name:
                    parts = base_name.split('_')
                    site_id = parts[2].replace('.txt', '')
                    output_file = f"GT_FULL_{site_id}_{timestamp}.txt"
                else:
                    output_file = f"Online_FULL_Converted_{timestamp}.txt"
            
            # 3. 온라인 형식 생성 (전체 레코드)
            online_data = self._create_online_format_from_tuples(records)
            
            # 4. 파일 저장 (Hex-String, 크기 제한 없음)
            hex_string = online_data.hex().upper()
            with open(output_file, 'w') as f:
                f.write(hex_string)
            
            input_record_count = len(records)
            output_record_count = input_record_count  # 변환 시 레코드 수는 동일
            
            return ConversionResult(
                success=True,
                output_file=output_file,
                record_count=output_record_count,
                message=f"오프라인 → 온라인(전체) 변환 성공: {output_record_count}개 레코드",
                input_record_count=input_record_count,
                output_record_count=output_record_count
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output_file="",
                record_count=0,
                message=f"변환 실패: {str(e)}"
            )
    
    def _create_online_format(self, record_data: bytes) -> bytes:
        """온라인 파일 형식 생성 (Raw 데이터)"""
        
        # 현재 타임스탬프
        now = datetime.now()
        file_timestamp = bytes([
            now.year % 100,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second
        ])
        
        # 헤더
        header = b'\x00\x0A'
        
        # 전체 구조
        online_data = file_timestamp + header + record_data
        
        # 518 bytes로 제한
        if len(online_data) > 518:
            online_data = online_data[:518]
        
        return online_data
    
    def _create_online_format_from_tuples(self, records: List[Tuple[datetime, bytes]]) -> bytes:
        """온라인 파일 형식 생성 (튜플 리스트로부터, 크기 제한 없음)"""
        
        # 현재 타임스탬프
        now = datetime.now()
        file_timestamp = bytes([
            now.year % 100,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second
        ])
        
        # 헤더
        header = b'\x00\x0A'
        
        # 레코드 데이터 생성 (모든 레코드 포함)
        record_data = b''
        for ts, record_bytes in records:
            # 오프라인 형식: [레코드타입][07][마커][타임스탬프][데이터]
            # 온라인 형식: [07][마커][타임스탬프][데이터]
            
            if len(record_bytes) >= 9:
                # 오프라인 형식인 경우 (레코드타입 + 07 + 마커 + 타임스탬프 + 데이터)
                if record_bytes[1:3] == b'\x07':  # 레코드타입 다음이 07
                    # 레코드 타입 제거하고 온라인 형식으로 변환
                    online_record = record_bytes[1:]  # 레코드 타입 제거
                    record_data += online_record
                elif record_bytes[0:2] == b'\x07':  # 이미 온라인 형식
                    record_data += record_bytes
                else:
                    # 마커 찾아서 재구성
                    marker_pos = record_bytes.find(b'\x07')
                    if marker_pos != -1 and marker_pos + 1 < len(record_bytes):
                        marker_byte = record_bytes[marker_pos + 1]
                        # 타임스탬프가 None이면 레코드 데이터에서 타임스탬프 추출 시도
                        if ts is not None:
                            ts_bytes = bytes([
                                ts.year % 100,
                                ts.month,
                                ts.day,
                                ts.hour,
                                ts.minute,
                                ts.second
                            ])
                        else:
                            # 타임스탬프가 없으면 레코드 데이터에서 추출 시도 (마커 뒤 6바이트)
                            if marker_pos + 8 <= len(record_bytes):
                                ts_bytes = record_bytes[marker_pos+2:marker_pos+8]
                                if len(ts_bytes) != 6:
                                    ts_bytes = b'\x00' * 6  # 기본값
                            else:
                                ts_bytes = b'\x00' * 6  # 기본값
                        data_start = marker_pos + 8  # 07 + 마커 + 타임스탬프(6)
                        record_data_part = record_bytes[data_start:] if data_start < len(record_bytes) else b''
                        online_record = b'\x07' + bytes([marker_byte]) + ts_bytes + record_data_part
                        record_data += online_record
            elif len(record_bytes) >= 8 and record_bytes[0:2] == b'\x07':
                # 이미 온라인 형식
                record_data += record_bytes
        
        # 전체 구조 (크기 제한 없음 - 전체 레코드 포함)
        online_data = file_timestamp + header + record_data
        
        return online_data
    
    # =====================================================================
    # 3. 병합 → 온라인 출력
    # =====================================================================
    
    def merge_to_online(
        self, 
        online_file: str, 
        offline_file: str, 
        output_file: str = None
    ) -> ConversionResult:
        """
        온라인 + 오프라인 파일 병합하여 온라인 형식으로 출력
        타임스탬프 기준 중복 제거
        
        Args:
            online_file: 온라인 파일 경로
            offline_file: 오프라인 파일 경로
            output_file: 출력 파일 경로
        
        Returns:
            ConversionResult
        """
        try:
            # 1. 두 파일에서 레코드 추출
            online_records = self._extract_records_from_online(online_file)
            offline_records = self._extract_records_from_offline(offline_file)
            
            # 2. 병합 및 중복 제거
            online_record_count = len(online_records)
            offline_record_count = len(offline_records)
            total_before_merge = online_record_count + offline_record_count
            
            merged_records = self._merge_and_deduplicate(online_records, offline_records)
            
            final_record_count = len(merged_records)
            duplicate_count = total_before_merge - final_record_count
            
            # 3. 출력 파일명 생성
            if output_file is None:
                timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
                output_file = f"Merged_Online_{timestamp}.txt"
            
            # 4. 온라인 형식으로 저장
            result = self._save_as_online(merged_records, output_file)
            
            return ConversionResult(
                success=True,
                output_file=output_file,
                record_count=final_record_count,
                message=f"병합 성공: {final_record_count}개 레코드 (중복 제거 완료)",
                input_record_count=total_before_merge,
                output_record_count=final_record_count,
                duplicate_count=duplicate_count,
                online_record_count=online_record_count,
                offline_record_count=offline_record_count
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output_file="",
                record_count=0,
                message=f"병합 실패: {str(e)}"
            )
    
    # =====================================================================
    # 4. 병합 → 오프라인 출력
    # =====================================================================
    
    def merge_to_offline(
        self, 
        online_file: str, 
        offline_file: str, 
        output_file: str = None
    ) -> ConversionResult:
        """
        온라인 + 오프라인 파일 병합하여 오프라인 형식으로 출력
        타임스탬프 기준 중복 제거
        
        Args:
            online_file: 온라인 파일 경로
            offline_file: 오프라인 파일 경로
            output_file: 출력 파일 경로
        
        Returns:
            ConversionResult
        """
        try:
            # 1. 두 파일에서 레코드 추출
            online_records = self._extract_records_from_online(online_file)
            offline_records = self._extract_records_from_offline(offline_file)
            
            # 2. 병합 및 중복 제거
            online_record_count = len(online_records)
            offline_record_count = len(offline_records)
            total_before_merge = online_record_count + offline_record_count
            
            merged_records = self._merge_and_deduplicate(online_records, offline_records)
            
            final_record_count = len(merged_records)
            duplicate_count = total_before_merge - final_record_count
            
            # 3. 출력 파일명 생성
            if output_file is None:
                timestamp = datetime.now().strftime('%y%m%d_%H%M%S')
                is_gt = 'GT' in offline_file or 'GT' in online_file
                prefix = 'Fault_GT' if is_gt else 'Fault_WBVF'
                output_file = f"{prefix}_Merged_{timestamp}.txt"
            
            # 4. 오프라인 형식으로 저장
            result = self._save_as_offline(
                merged_records, 
                output_file,
                is_gt='GT' in offline_file or 'GT' in online_file
            )
            
            return ConversionResult(
                success=True,
                output_file=output_file,
                record_count=final_record_count,
                message=f"병합 성공: {final_record_count}개 레코드 (중복 제거 완료)",
                input_record_count=total_before_merge,
                output_record_count=final_record_count,
                duplicate_count=duplicate_count,
                online_record_count=online_record_count,
                offline_record_count=offline_record_count
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                output_file="",
                record_count=0,
                message=f"병합 실패: {str(e)}"
            )
    
    # =====================================================================
    # 헬퍼 함수들
    # =====================================================================
    
    def _extract_records_from_online(self, filepath: str) -> List[Tuple[datetime, bytes]]:
        """온라인 파일에서 레코드 추출"""
        records = []
        
        # 파일 타입 자동 감지
        with open(filepath, 'rb') as f:
            raw_data = f.read()
        
        # Binary 파일인지 확인 (오프라인 파일)
        # 온라인 파일은 Hex-String이므로 ASCII로 디코딩 가능해야 함
        try:
            hex_string = raw_data.decode('ascii').strip()
            # Hex-String인지 확인 (0-9, A-F, a-f, 공백, 개행만 포함)
            hex_chars = set(b'0123456789ABCDEFabcdef\n\r\t ')
            sample = raw_data[:min(100, len(raw_data))]
            if not all(c in hex_chars for c in sample):
                # Binary 파일로 판단
                raise UnicodeDecodeError('ascii', raw_data, 0, 1, 'not ascii')
        except (UnicodeDecodeError, AttributeError):
            # Binary 파일이면 오프라인 추출 함수로 처리
            return self._extract_records_from_offline(filepath)
        
        # Hex-String이면 계속 처리
        binary_data = bytes.fromhex(hex_string)
        
        # 파일 타임스탬프와 헤더 건너뛰기 (처음 8바이트)
        data_start = 8
        if len(binary_data) > data_start:
            binary_data = binary_data[data_start:]
        
        # 마커 찾기
        markers = [b'\x07\xE9', b'\x07\xEA', b'\x07\xEB', b'\x07\xE7']
        all_marker_positions = []
        
        # 모든 마커 위치 찾기
        for marker in markers:
            pos = 0
            while True:
                pos = binary_data.find(marker, pos)
                if pos == -1:
                    break
                all_marker_positions.append(pos)
                pos += 1
        
        # 마커 위치 정렬
        all_marker_positions.sort()
        
        # 각 마커에서 레코드 추출 (타임스탬프 검증 완화)
        for i, pos in enumerate(all_marker_positions):
            # 타임스탬프 추출 (마커 뒤 6바이트)
            ts = None
            if pos + 8 <= len(binary_data):
                ts_bytes = binary_data[pos+2:pos+8]
                if len(ts_bytes) == 6:
                    try:
                        yy, mm, dd, hh, mi, ss = ts_bytes
                        # 타임스탬프 검증 완화: 기본적인 범위만 확인
                        if (0 <= yy <= 99 and 0 <= mm <= 12 and 0 <= dd <= 31 and
                            0 <= hh < 24 and 0 <= mi < 60 and 0 <= ss < 60):
                            try:
                                ts = datetime(2000 + yy, mm, dd, hh, mi, ss)
                            except:
                                # 날짜가 유효하지 않아도 레코드는 포함
                                pass
                    except:
                        pass
            
            # 레코드 데이터: 다음 마커까지 또는 최대 100바이트
            if i + 1 < len(all_marker_positions):
                # 다음 마커가 있으면 그 전까지
                record_end = all_marker_positions[i + 1]
            else:
                # 마지막 레코드면 최대 100바이트 또는 파일 끝까지
                record_end = min(pos + 100, len(binary_data))
            
            record_data = binary_data[pos:record_end]
            
            if len(record_data) >= 8:  # 최소 마커 + 타임스탬프
                # 타임스탬프가 없어도 레코드는 포함 (타임스탬프는 None으로 유지)
                records.append((ts, record_data))
        
        return records
    
    def _extract_records_from_offline(self, filepath: str) -> List[Tuple[datetime, bytes]]:
        """오프라인 파일에서 레코드 추출"""
        records = []
        
        with open(filepath, 'rb') as f:
            binary_data = f.read()
        
        # ConfigDone 헤더 이후부터 시작 (약 7000바이트 이후)
        # 실제 레코드 데이터는 보통 7000바이트 이후부터 시작
        data_start = 0
        config_done_pos = binary_data.find(b'ConfigDone')
        if config_done_pos != -1:
            # ConfigDone 이후 인덱스 테이블을 건너뛰고 레코드 영역으로 이동
            # 인덱스 테이블은 약 200바이트, 설정 데이터 포함 약 7000바이트
            data_start = max(7000, config_done_pos + 1000)
        
        if data_start > 0:
            binary_data = binary_data[data_start:]
        
        # 마커 찾기
        markers = [b'\x07\xE4', b'\x07\xE5', b'\x07\xE6', b'\x07\xE7', b'\x07\xE8', b'\x07\xE9']
        all_marker_positions = []
        
        # 모든 마커 위치 찾기 (레코드 타입 검증 완화)
        for marker in markers:
            pos = 0
            while True:
                pos = binary_data.find(marker, pos)
                if pos == -1:
                    break
                # 레코드 타입 바이트 확인 (마커 앞 1바이트)
                if pos > 0:
                    rec_type = binary_data[pos - 1]
                    # 레코드 타입 검증 완화: 0x00-0xFF 범위 모두 허용 (너무 엄격한 필터링 제거)
                    # 단, 0x00은 제외 (일반적으로 유효하지 않음)
                    if rec_type != 0:
                        all_marker_positions.append(pos - 1)  # 레코드 타입 포함
                else:
                    # 파일 시작 부분의 마커도 포함
                    all_marker_positions.append(pos)
                pos += 1
        
        # 마커 위치 정렬
        all_marker_positions.sort()
        
        # 각 레코드 추출 (타임스탬프 검증 완화)
        for i, rec_start in enumerate(all_marker_positions):
            # rec_start가 음수일 수 있으므로 조정
            if rec_start < 0:
                marker_pos = 0
            else:
                marker_pos = rec_start + 1  # 레코드 타입 다음이 마커
            
            # 타임스탬프 추출 (마커 뒤 6바이트)
            ts = None
            if marker_pos + 8 <= len(binary_data):
                ts_bytes = binary_data[marker_pos+2:marker_pos+8]
                if len(ts_bytes) == 6:
                    try:
                        yy, mm, dd, hh, mi, ss = ts_bytes
                        # 타임스탬프 검증 완화: 기본적인 범위만 확인
                        if (0 <= yy <= 99 and 0 <= mm <= 12 and 0 <= dd <= 31 and
                            0 <= hh < 24 and 0 <= mi < 60 and 0 <= ss < 60):
                            try:
                                ts = datetime(2000 + yy, mm, dd, hh, mi, ss)
                            except:
                                # 날짜가 유효하지 않아도 레코드는 포함 (예: 2월 30일 등)
                                # 타임스탬프는 None으로 유지
                                pass
                    except:
                        pass
            
            # 레코드 데이터: 다음 레코드까지 또는 최대 100바이트
            if i + 1 < len(all_marker_positions):
                # 다음 레코드가 있으면 그 전까지
                record_end = all_marker_positions[i + 1]
            else:
                # 마지막 레코드면 최대 100바이트 또는 파일 끝까지
                record_end = min(rec_start + 100, len(binary_data))
            
            record_data = binary_data[max(0, rec_start):record_end]
            
            if len(record_data) >= 8:  # 최소 마커 + 타임스탬프 (레코드 타입 없어도 OK)
                # 타임스탬프가 없어도 레코드는 포함 (타임스탬프는 None으로 유지)
                records.append((ts, record_data))
        
        return records
    
    def _merge_and_deduplicate(
        self, 
        records1: List[Tuple[datetime, bytes]], 
        records2: List[Tuple[datetime, bytes]]
    ) -> List[Tuple[datetime, bytes]]:
        """두 레코드 리스트 병합 및 중복 제거
        
        중복 제거 규칙:
        - 온라인 파일과 오프라인 파일 간의 중복만 제거
        - 타임스탬프 + 데이터가 정확히 같을 때만 중복으로 간주
        - 같은 타임스탬프라도 데이터가 다르면 별도 레코드로 취급
        - 같은 파일 내의 중복은 제거하지 않음
        """
        
        # 타임스탬프가 있는 레코드와 없는 레코드 분리
        records1_with_ts = []
        records1_without_ts = []
        records2_with_ts = []
        records2_without_ts = []
        
        for ts, data in records1:
            if ts is not None:
                records1_with_ts.append((ts, data))
            else:
                records1_without_ts.append((ts, data))
        
        for ts, data in records2:
            if ts is not None:
                records2_with_ts.append((ts, data))
            else:
                records2_without_ts.append((ts, data))
        
        # 온라인 파일(records1)의 레코드를 기준으로 오프라인 파일(records2)과 비교
        # 타임스탬프 + 데이터가 정확히 같은 경우만 중복으로 간주
        
        # records1의 모든 레코드를 set으로 변환 (빠른 조회를 위해)
        records1_set = {(ts, data) for ts, data in records1_with_ts}
        
        # records1의 모든 레코드 포함 (같은 파일 내 중복은 제거하지 않음)
        merged_with_ts = list(records1_with_ts)
        
        # records2에서 records1과 정확히 같은 레코드만 제외하고 나머지는 모두 포함
        for ts, data in records2_with_ts:
            # records1에 정확히 같은 레코드(타임스탬프 + 데이터)가 없으면 포함
            if (ts, data) not in records1_set:
                merged_with_ts.append((ts, data))
        
        # 타임스탬프 기준 정렬
        merged_with_ts.sort(key=lambda x: x[0] if x[0] is not None else datetime.min)
        
        # 타임스탬프가 없는 레코드는 모두 포함 (중복 제거 안 함, 정렬 안 함)
        result = merged_with_ts + records1_without_ts + records2_without_ts
        
        return result
    
    def _save_as_online(self, records: List[Tuple[datetime, bytes]], output_file: str):
        """레코드를 온라인 형식으로 저장"""
        
        # 파일 타임스탬프
        now = datetime.now()
        file_timestamp = bytes([
            now.year % 100,
            now.month,
            now.day,
            now.hour,
            now.minute,
            now.second
        ])
        
        # 헤더
        header = b'\x00\x0A'
        
        # 레코드 데이터 결합 (모든 레코드 포함, 온라인 형식에 맞게 변환)
        record_data = b''
        for ts, data in records:
            # 오프라인 형식([레코드타입][07][마커][타임스탬프][데이터])을 
            # 온라인 형식([07][마커][타임스탬프][데이터])으로 변환
            if len(data) >= 9 and data[1:3] == b'\x07':  # 레코드타입 + 07 + 마커
                # 레코드 타입 제거하고 온라인 형식으로 변환
                online_record = data[1:]  # 레코드 타입 제거
                record_data += online_record
            elif len(data) >= 8 and data[0:2] == b'\x07':  # 이미 온라인 형식
                record_data += data
            else:
                # 형식 변환 필요
                marker_pos = data.find(b'\x07')
                if marker_pos != -1 and marker_pos + 1 < len(data):
                    marker_byte = data[marker_pos + 1]
                    # 타임스탬프가 None이면 레코드 데이터에서 타임스탬프 추출 시도
                    if ts is not None:
                        ts_bytes = bytes([
                            ts.year % 100,
                            ts.month,
                            ts.day,
                            ts.hour,
                            ts.minute,
                            ts.second
                        ])
                    else:
                        # 타임스탬프가 없으면 레코드 데이터에서 추출 시도 (마커 뒤 6바이트)
                        if marker_pos + 8 <= len(data):
                            ts_bytes = data[marker_pos+2:marker_pos+8]
                            if len(ts_bytes) != 6:
                                ts_bytes = b'\x00' * 6  # 기본값
                        else:
                            ts_bytes = b'\x00' * 6  # 기본값
                    data_part = data[marker_pos + 8:] if marker_pos + 8 < len(data) else b''
                    online_record = b'\x07' + bytes([marker_byte]) + ts_bytes + data_part
                    record_data += online_record
        
        # 전체 데이터
        online_data = file_timestamp + header + record_data
        
        # 병합 결과는 모든 레코드를 포함 (크기 제한 없음)
        # 일반 온라인 파일은 518바이트 제한이지만, 병합 결과는 전체 데이터 포함
        
        # Hex-String으로 저장
        hex_string = online_data.hex().upper()
        with open(output_file, 'w') as f:
            f.write(hex_string)
    
    def _save_as_offline(self, records: List[Tuple[datetime, bytes]], output_file: str, is_gt: bool = True):
        """레코드를 오프라인 형식으로 저장"""
        
        # ConfigDone 헤더 (10 bytes)
        config_done = b'ConfigDone'
        
        # 설정 데이터 영역 (32 bytes, 오프셋 10-41)
        config_area_1 = b'\x00' * 32
        
        # 시스템 식별자 (오프셋 42부터)
        if is_gt:
            identifier = b'GSP'  # 3 bytes
            config_area_2 = b'\x00' * 228  # 오프셋 45-272 (228 bytes)
        else:
            identifier = b'WBVF'  # 4 bytes
            config_area_2 = b'\x00' * 227  # 오프셋 46-272 (227 bytes)
        
        # 인덱스 테이블 (200 bytes, 오프셋 273-472)
        index_table = b'\x00\x00' + b'B2\x00B1\x00' + b'1\x00\x002\x00\x003\x00\x00'
        index_table += b'\x00' * (200 - len(index_table))
        
        # 레코드 데이터 시작 위치까지 패딩 (~7000 오프셋)
        record_start_padding = b'\x00' * (7000 - len(config_done) - len(config_area_1) - len(identifier) - len(config_area_2) - len(index_table))
        
        # 레코드 데이터 결합
        record_data = b''
        for ts, data in records:
            record_data += data
        
        # 전체 구조
        offline_data = config_done + config_area_1 + identifier + config_area_2 + index_table + record_start_padding + record_data
        
        # 목표 크기로 패딩
        target_size = 524288 if is_gt else 262144
        if len(offline_data) < target_size:
            offline_data += b'\x00' * (target_size - len(offline_data))
        else:
            offline_data = offline_data[:target_size]
        
        # Binary로 저장
        with open(output_file, 'wb') as f:
            f.write(offline_data)


# 테스트 코드
if __name__ == '__main__':
    converter = FDCNEOConverter()
    
    print("=" * 80)
    print("FDC NEO Converter 테스트")
    print("=" * 80)
    
    # 테스트 1: 온라인 → 오프라인
    print("\n[테스트 1] 온라인 → 오프라인")
    result = converter.online_to_offline('GT_test.txt', 'Fault_GT_converted.txt')
    print(f"결과: {result.message}")
    
    # 테스트 2: 오프라인 → 온라인
    print("\n[테스트 2] 오프라인 → 온라인")
    result = converter.offline_to_online('Fault_GT_test.txt', 'GT_converted.txt')
    print(f"결과: {result.message}")
