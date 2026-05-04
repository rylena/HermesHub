import numpy as np
import pytest

from hermeshub.sherpa_test import int16_samples_to_float32, sherpa_model_paths


def test_int16_samples_to_float32_resamples_to_target_rate():
    samples = np.arange(44100, dtype=np.int16)

    result = int16_samples_to_float32(samples, source_sample_rate=44100, target_sample_rate=16000)

    assert result.dtype == np.float32
    assert len(result) == 16000


def test_sherpa_model_paths_reports_missing_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        sherpa_model_paths(tmp_path)
