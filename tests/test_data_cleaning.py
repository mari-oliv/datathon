import pytest
import pandas as pd
from src.data_cleaning import clean_discovery_data


@pytest.fixture
def sample_df():
    # GIVEN
    return pd.DataFrame({"Ano nasc": [2010], "Nome": ["Ana"], "Outra Coluna": [123]})

class TestCleanDiscoveryData:
    def test_renames_columns(self, sample_df):
        result = clean_discovery_data(sample_df)

        assert "Ano de Nascimento do Aluno" in result.columns
        assert "Ano nasc" not in result.columns

    def test_drops_nome_column(self, sample_df):

        result = clean_discovery_data(sample_df)

        assert "Nome" not in result.columns

    def test_keeps_unmapped_columns(self, sample_df):

        result = clean_discovery_data(sample_df)

        assert "Outra Coluna" in result.columns
