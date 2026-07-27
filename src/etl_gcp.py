import os
import json
from google.oauth2 import service_account
from google.cloud import billing_v1


# Caminho da chave da Service Account
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CREDENTIALS_PATH = os.path.join(
    BASE_DIR,
    "data",
    "earnest-dogfish-503718-b6-b096d1d56f8e.json"
)


# Carrega credenciais
credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_PATH
)


# Cliente da API Cloud Billing
billing_client = billing_v1.CloudBillingClient(
    credentials=credentials
)


def listar_contas_billing():
    """
    Lista contas de faturamento disponíveis
    """

    print("\nContas de Billing encontradas:\n")

    request = billing_v1.ListBillingAccountsRequest()

    accounts = billing_client.list_billing_accounts(
        request=request
    )

    for account in accounts:
        print(f"Nome: {account.name}")
        print(f"Display Name: {account.display_name}")
        print(f"Open: {account.open_}")
        print("-" * 50)


def verificar_projeto(project_id):
    """
    Verifica o vínculo do projeto com Billing
    """

    project_name = f"projects/{project_id}"

    response = billing_client.get_project_billing_info(
        name=project_name
    )

    print("\nInformações de Billing do projeto:\n")
    print(response)


if __name__ == "__main__":

    print("Iniciando ETL GCP...")

    listar_contas_billing()

    # Coloque seu PROJECT_ID aqui
    PROJECT_ID = "SEU_PROJECT_ID"

    # Descomente quando tiver o ID correto
    # verificar_projeto(PROJECT_ID)

    print("\nETL GCP finalizado.")
