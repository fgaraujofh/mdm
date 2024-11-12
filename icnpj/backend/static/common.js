$(document).ready(function() {
    // Recuperar o token do localStorage, caso exista
     let token = localStorage.getItem("auth_token");

    // Exibir o formulário de consulta se o token já estiver presente
    if (token) {
        $("#login-card").hide();
        $("#consulta_card").show();
    }

    // Função de login
    $("#login").click(function(e) {
        e.preventDefault();

        $.ajax({
            type: "POST",
            url: "/login",  // Use URL relativa para evitar problemas de CORS
            data: {
                username: $("#username").val(),
                password: $("#password").val()
            },
            success: function(response) {
                // Exibir o formulário de consulta após o login bem-sucedido
                $("#login-card").fadeOut("normal");
                $("#consulta_card").fadeIn("normal");
                
                $("#alert-message").removeClass("alert-danger").addClass("alert-success");
                $("#alert-message").text("Login com sucesso").show();

                // Armazenar o token no localStorage
                localStorage.setItem("auth_token", response.token);
                token = response.token;  // Atualizar a variável token
            },
            error: function(xhr, status, error) {
                const response_parsed = JSON.parse(xhr.responseText);
                $("#error-message").addClass("alert-danger").text(response_parsed.error).show();
            }
        });
        return false;
    });

    // Função de consulta
    $("#consulta").click(function(e) {
        e.preventDefault();

        if (!token) {
            $("#error-message-consulta").addClass("alert-danger").text("Token de autenticação não encontrado. Faça login novamente.").show();
            return;
        }

        $.ajax({
            type: "POST",
            url: "/search",  // Use URL relativa
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader('Authorization', token);
            },
            data: {
                cnpjs: $("#lista_cnpjs").val(),
            },
            success: function(response) {
                console.log(response);

                // Usar response para desenhar tabela ou outra exibição de dados
                // Parseando o JSON retornado
                const jsonResponse = response;

                // Limpa o contêiner de tabelas antes de renderizar novas tabelas
                $("#tabelas-container").empty();

                // Iterar sobre cada "Alvo" no JSON
                Object.keys(jsonResponse).forEach(function(alvo) {
                    const data = jsonResponse[alvo];  // Conjunto de dados para o "Alvo" atual

                    // Adicionar um título para o alvo
                    let tableHTML = `<h3>${alvo}</h3>`;

                    // Criar a tabela com cabeçalho
                    tableHTML += `
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>CEP</th>
                                    <th>Logradouro</th>
                                    <th>CPF Responsável</th>
                                    <th>Telefone 1</th>
                                    <th>Email</th>
                                    <th>CNAE</th>
                                    <th>Nome Sim</th>
                                    <th>Nome Fantasia</th>
                                    <th>Detalhe</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    // Iterar sobre cada item nos dados do "Alvo"
                    data.forEach(function(item) {
                        tableHTML += `
                            <tr>
                                <td>${item.id}</td>
                                <td>${item.cep ? "✔️" : "❌"}</td>
                                <td>${item.logradouro ? "✔️" : "❌"}</td>
                                <td>${item.cpfResponsavel ? "✔️" : "❌"}</td>
                                <td>${item.telefone1 ? "✔️" : "❌"}</td>
                                <td>${item.email ? "✔️" : "❌"}</td>
                                <td>${item.cnae ? "✔️" : "❌"}</td>
                                <td>${item.nomeSim}</td>
                                <td>${item.nomeFantasia}</td>
                                <td>
                                    <button class="btn btn-secondary btn-sm" onclick="abrirTR('tabela_${item.id_alvo}_${item.id}', this, '${token}')">&#9660;</button>
                                </td>
                            </tr>
                            <tr id="tabela_${item.id_alvo}_${item.id}" style="display: none;">
                            </tr>
                        `;
                    });

                    // Fechar a tabela
                    tableHTML += `
                            </tbody>
                        </table>
                    `;

                    // Adicionar a tabela completa ao contêiner
                    $("#tabelas-container").append(tableHTML);
                });

                $("#error-message-consulta").hide();
            },
            error: function(xhr, status, error) {
                const response_parsed = JSON.parse(xhr.responseText);
                $("#error-message-consulta").addClass("alert-danger").text(response_parsed.error).show();
                localStorage.removeItem("auth_token");
                $("#login-card").show();
                $("#consulta_card").hide();
            }
        });
        return false;
    });
});

// Função abrir TR de comparacao
function abrirTR(trId, button, token) {
    const trElement = document.getElementById(trId);

    // Verificar se o <tr> já possui conteúdo
    if (trElement.innerHTML.trim() === "") {
        // Extrair os dois IDs do <tr>
        const ids = trId.replace("tabela_", "").split("_");
        const cnpjs = `${ids[0]}, ${ids[1]}`;

        console.log(cnpjs)

        if (!token) {
            $("#error-message-consulta").addClass("alert-danger").text("Token de autenticação não encontrado. Faça login novamente.").show();
            return;
        }
        // Fazer a requisição POST para a API de comparação
        $.ajax({
            type: "POST",
            url: "/compare",  // URL do serviço
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader('Authorization', token);  // Token de autorização
            },
            data: {
                cnpjs: cnpjs  // Passar os dois CNPJs
            },
            success: function(response) {
                console.log(response)
                // Montar a tabela com o conteúdo comparado
                let tableContent = `
                    <td colspan="100%">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th></th>
                                    <th>Empresa Alvo</th>
                                    <th>Empresa Comparada</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                // Função para adicionar linhas à tabela
                function addRow(campo, valor1, valor2) {
                    tableContent += `
                        <tr>
                            <td><b>${campo}</b></td>
                            <td>${valor1 || 'N/A'}</td>
                            <td>${valor2 || 'N/A'}</td>
                        </tr>
                    `;
                }

                // Adicionar os CNPJs
                addRow("CNPJ", formatarCNPJ(ids[0]), formatarCNPJ(ids[1]));
                // Adicionar os demais dados
                const dadosEm = response.te_dados_em;
                const dadosEs = response.te_dados_es;

                addRow("Nome Empresarial", dadosEm.nomeEmpresarial.registro1, dadosEm.nomeEmpresarial.registro2);
                addRow("Nome Fantasia", dadosEs.nomeFantasia.registro1, dadosEs.nomeFantasia.registro2);
                addRow("Situação Cadastral", formatarSituacaoCadastral(dadosEs.situacaoCadastral.registro1), 
                                             formatarSituacaoCadastral(dadosEs.situacaoCadastral.registro2));
                addRow("CPF Responsável", formatarCPF(dadosEm.cpfResponsavel.registro1), formatarCPF(dadosEm.cpfResponsavel.registro2));
                addRow("Qualificação Responsável", formatarClassificacaoResponsavel(dadosEm.qualificacaoResponsavel.registro1), 
                                                   formatarClassificacaoResponsavel(dadosEm.qualificacaoResponsavel.registro2));
                addRow("Email", dadosEs.email.registro1, dadosEs.email.registro2);
                addRow("Capital Social", formatarMoeda(dadosEm.capitalSocial.registro1), formatarMoeda(dadosEm.capitalSocial.registro2));
                addRow("Porte Empresa", formatarPorte(dadosEm.porteEmpresa.registro1), formatarPorte(dadosEm.porteEmpresa.registro2));
                addRow("Natureza Jurídica", formataNatureza(dadosEm.naturezaJuridica.registro1), formataNatureza(dadosEm.naturezaJuridica.registro2));
                
                // addRow("Tipo Logradouro", dadosEs.tipoLogradouro.registro1, dadosEs.tipoLogradouro.registro2);
                addRow("UF", dadosEs.uf.registro1, dadosEs.uf.registro2);
                addRow("Município", dadosEs.municipio.registro1, dadosEs.municipio.registro2);
                addRow("Bairro", dadosEs.bairro.registro1, dadosEs.bairro.registro2);
                addRow("Logradouro", dadosEs.logradouro.registro1, dadosEs.logradouro.registro2);
                addRow("Número", dadosEs.numero.registro1, dadosEs.numero.registro2);
                addRow("Telefone Principal", dadosEs.telefone1.registro1, dadosEs.telefone1.registro2);
                addRow("CEP", dadosEs.cep.registro1, dadosEs.cep.registro2);
                // addRow("Data Situação Cadastral", dadosEs.dataSituacaoCadastral.registro1, dadosEs.dataSituacaoCadastral.registro2);

                // Fechar a tabela
                tableContent += `
                            </tbody>
                        </table>
                    </td>
                `;

                // Exibir o conteúdo no <tr> abaixo do botão clicado
                trElement.innerHTML = tableContent;
                $(trElement).show();  // Mostrar o <tr>
            },
            error: function(xhr, status, error) {
                const response_parsed = JSON.parse(xhr.responseText);
                alert("Erro ao buscar a comparação: " + response_parsed.error);
            }
        });
        }

    // Exibe o trElement
    trElement.style.display = 'table-row';
    // Altera o botão para mostrar a seta para cima
    button.innerHTML = '&#9650;'; // Seta para cima
    // Altera a função onclick para fechar o div
    button.setAttribute('onclick', `fecharTR('${trId}', this, '${token}')`);
}
    
// Função para fechar o div e alterar a seta
function fecharTR(trId, button, token) {
    var trElement = document.getElementById(trId);
    // Oculta o div
    trElement.style.display = 'none';
    // Altera o botão para mostrar a seta para baixo
    button.innerHTML = '&#9660;'; // Seta para baixo
    // Altera a função onclick para abrir o div novamente
    button.setAttribute('onclick', `abrirTR('${trId}', this, '${token}')`);
}

function formatarCPF(cpfRaw) {
    // Remover qualquer caractere que não seja número
    cpfRaw = cpfRaw.replace(/\D/g, '');

    // Verificar se o CPF tem 11 dígitos
    if (cpfRaw.length !== 11) {
        return cpfRaw;
    }

    // Aplicar a formatação
    const cpfFormatado = cpfRaw.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
    
    return cpfFormatado;
}

function formatarMoeda(valorRaw) {
    // Remover zeros à esquerda
    let valorNumerico = parseInt(valorRaw, 10);

    // Converter o número para o formato de moeda brasileira
    let valorFormatado = valorNumerico.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    });

    return valorFormatado;
}

function formatarPorte(codigoPorte) {
    // Mapeamento dos códigos de porte para suas descrições
    const portes = {
        '00': '00 - NÃO INFORMADO',
        '01': '01 - MICRO EMPRESA',
        '03': '03 - EMPRESA DE PEQUENO PORTE',
        '05': '05 - DEMAIS'
    };

    // Verifica se o código é válido, caso contrário, retorna 'Código inválido'
    return portes[codigoPorte] || codigoPorte;
}

function formataNatureza(codigoNatureza) {
    // Mapeamento dos códigos de natureza jurídica para suas descrições
    const naturezas = {
        '2011': 'Empresa Pública',
        '2038': 'Sociedade de Economia Mista',
        '2046': 'Sociedade Anônima Aberta',
        '2054': 'Sociedade Anônima Fechada',
        '2062': 'Sociedade Empresária Limitada',
        '2070': 'Sociedade Empresária em Nome Coletivo',
        '2089': 'Sociedade Empresária em Comandita Simples',
        '2097': 'Sociedade Empresária em Comandita por Ações',
        '2127': 'Sociedade em Conta de Participação',
        '2143': 'Cooperativa',
        '2151': 'Consórcio de Sociedades',
        '2160': 'Grupo de Sociedades',
        '2232': 'Sociedade Simples Pura',
        '2240': 'Sociedade Simples Limitada',
        '2259': 'Sociedade Simples em Nome Coletivo',
        '2267': 'Sociedade Simples em Comandita Simples',
        '2291': 'Consórcio Simples',
        '2305': 'Empresa Individual de Responsabilidade Limitada (de Natureza Empresária)',
        '2313': 'Empresa Individual de Responsabilidade Limitada (de Natureza Simples)',
        '3069': 'Fundação Privada',
        '3220': 'Organização Religiosa',
        '3301': 'Organização Social (OS)',
        '3999': 'Associação Privada',
        '4120': 'Produtor Rural (Pessoa Física)'
    };

    // Verifica se o código é válido, caso contrário, retorna 'Código inválido'
    return naturezas[codigoNatureza] || codigoNatureza;
}

function calcularDV(cnpjBase) {
    // Adicionar a parte do estabelecimento '0001'
    const cnpjSemDV = cnpjBase + '0001';

    // Pesos para o cálculo do primeiro e segundo dígito verificador
    const pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
    const pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];

    // Função para calcular o dígito verificador
    function calcularDigito(pesos, numeros) {
        let soma = 0;
        for (let i = 0; i < pesos.length; i++) {
            soma += pesos[i] * parseInt(numeros[i]);
        }
        const resto = soma % 11;
        return resto < 2 ? 0 : 11 - resto;
    }

    // Primeiro dígito verificador
    const primeiroDV = calcularDigito(pesos1, cnpjSemDV);
    
    // Segundo dígito verificador
    const segundoDV = calcularDigito(pesos2, cnpjSemDV + primeiroDV);

    // Retorna os dígitos verificadores
    return `${primeiroDV}${segundoDV}`;
}

function formatarCNPJ(cnpjBase) {
    // Certificar que o cnpjBase tem 8 dígitos
    if (cnpjBase.length !== 8) {
        return cnpjBase;
    }

    // Calcular o DV
    const dv = calcularDV(cnpjBase);

    // Montar o CNPJ completo com formatação
    const cnpjCompleto = cnpjBase + '0001' + dv;

    // Aplicar a formatação no padrão CNPJ (XX.XXX.XXX/0001-XX)
    const cnpjFormatado = cnpjCompleto.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, "$1.$2.$3/$4-$5");

    return cnpjFormatado;
}

function formatarClassificacaoResponsavel(codigoClassificacao) {
    // Mapeamento dos códigos de classificação para suas descrições
    const classificacoes = {
        '37': 'Sócio Pessoa Jurídica Domiciliado no Exterior',
        '38': 'Sócio Pessoa Física Residente ou Domiciliado no Exterior',
        '55': 'Sócio Comanditado Residente no Exterior',
        '56': 'Sócio Comanditário Pessoa Física Residente no Exterior',
        '57': 'Sócio Comanditário Pessoa Jurídica Domiciliado no Exterior',
        '65': 'Titular Pessoa Física Domiciliada no Brasil',
        '66': 'Titular Pessoa Física Residente ou Domiciliado no Exterior',
        '70': 'Administrador Residente ou Domiciliado no Exterior',
        '71': 'Conselheiro de Administração Residente ou Domiciliado no Exterior',
        '72': 'Diretor Residente ou Domiciliado no Exterior',
        '73': 'Presidente Residente ou Domiciliado no Exterior',
        '74': 'Sócio-Administrador Residente ou Domiciliado no Exterior',
        '75': 'Fundador Residente ou Domiciliado no Exterior',
        '78': 'Titular Pessoa Jurídica Domiciliada no Brasil',
        '79': 'Titular Pessoa Jurídica Domiciliada no Exterior',
        '30': 'Sócio Menor assistido/representado',
        '68': 'Titular Pessoa Física Menor (Assistido/Representado)',
        '29': 'Sócio Incapaz ou Relativamente Incapaz - exceto menor',
        '58': 'Sócio Comanditário Incapaz',
        '67': 'Titular Pessoa Física Incapaz ou Relativamente Incapaz (exceto menor)',
        '22': 'Sócio',
        '10': 'Diretor',
        '16': 'Presidente',
        '05': 'Administrador',
        '08': 'Conselheiro de Administração',
        '49': 'Sócio-Administrador',
        '52': 'Sócio com Capital',
        '53': 'Sócio sem Capital'
    };

    // Verifica se o código é válido, caso contrário, retorna 'Código não encontrado'
    const descricao = classificacoes[codigoClassificacao];
    if (descricao) {
        return `${codigoClassificacao} - ${descricao}`;
    } else {
        return codigoClassificacao;
    }
}

function formatarSituacaoCadastral(codigoSituacao) {
    // Mapeamento dos códigos de situação cadastral para suas descrições
    const situacoes = {
        '01': 'NULA',
        '02': 'ATIVA',
        '03': 'SUSPENSA',
        '04': 'INAPTA',
        '08': 'BAIXADA'
    };

    // Verifica se o código é válido, caso contrário, retorna 'Código não encontrado'
    const descricao = situacoes[codigoSituacao];
    if (descricao) {
        return `${codigoSituacao} - ${descricao}`;
    } else {
        return codigoSituacao;
    }
}