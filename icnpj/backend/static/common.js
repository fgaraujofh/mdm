$(document).ready(function() {
    // Recuperar o token do localStorage, caso exista
     let token = localStorage.getItem("auth_token");

    // Exibir o formulário de consulta se o token já estiver presente
    if (token) {
        $("#login-card").hide();
        $("#consulta_card").show();
    }

    // Função de logout
    $("#sair").click(function(e) {
        e.preventDefault();

        // Limpa todas as mensagens antes de sair
        limparMensagensTela();
        esvaziarTabelas();
        
        // Remover o token do localStorage
        localStorage.removeItem("auth_token");
        // Esconder o div de consulta
        $("#consulta_card").hide();
        // Mostrar o div de login
        $("#login-card").fadeIn("normal");

        // Exibir uma mensagem de logout bem-sucedido
        $("#alert-message").removeClass("alert-danger").addClass("alert-success");
        $("#alert-message").text("Você saiu com sucesso.").show();
    });

    
    // Função de login
    $("#login").click(function(e) {
        e.preventDefault();

        // Limpa as mensagens antes de exibir qualquer nova
        limparMensagensTela();
        esvaziarTabelas();

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

        // Limpa as mensagens antes de exibir qualquer nova
        limparMensagensTela();
        // Limpa o contêiner de tabelas antes de renderizar novas tabelas
        esvaziarTabelas();

        if (!token) {
            $("#error-message-consulta").addClass("alert-danger").text("Token de autenticação não encontrado. Faça login novamente.").show();
            return;
        }

        // Exibe o ícone de carregamento e desativa os botões
        $("#loading").show();
        $("#consulta, #sair").prop("disabled", true);

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

                let primeiroAlvo = true;  // Flag para verificar a primeira ocorrência
                let totalAlvos = Object.keys(jsonResponse).length;  // Quantidade de alvos

                // Iterar sobre cada "Alvo" no JSON
                Object.keys(jsonResponse).forEach(function(alvo) {
                    const data = jsonResponse[alvo];  // Conjunto de dados para o "Alvo" atual
                    let tableHTML = "";

                     // Criar o título do Alvo (h3)
                    if (primeiroAlvo) {
                        let totalItensPrimeiroAlvo = data.length;  // Número de itens do primeiro alvo

                        tableHTML += `
                            <h3 class="d-flex justify-content-between align-items-center">
                                <span>${formatarTextoAlvo(alvo)}</span>
                                <span>
                                    <i id="like-icon" class="far fa-thumbs-up text-success me-2" onclick="toggleLike()" data-bs-toggle="tooltip" title="Marcar como útil"></i>
                                    <i id="dislike-icon" class="far fa-thumbs-down text-danger me-3" onclick="toggleDislike()" data-bs-toggle="tooltip" title="Não é relevante"></i>
                                    <i class="fas fa-crosshairs text-danger" data-bs-toggle="tooltip" title="PJs Alvo"></i> ${totalAlvos} 
                                    <i class="fas fa-search text-primary" data-bs-toggle="tooltip" title="PJs Localizadas"></i> ${totalItensPrimeiroAlvo}
                                </span>
                            </h3>
                        `;
                        primeiroAlvo = false;  // Marcar que já tratamos o primeiro alvo
                    } else {
                        tableHTML += `<h3>${formatarTextoAlvo(alvo)}</h3>`;
                    }
                    
                    // Criar a tabela com cabeçalho
                    tableHTML += `
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th class="text-center">CEP</th>
                                    <th class="text-center">Logradouro</th>
                                    <th class="text-center">CPF Responsável</th>
                                    <th class="text-center">Telefone 1</th>
                                    <th class="text-center">Email</th>
                                    <th class="text-center">CNAE</th>
                                    <th class="text-center">Sócios Comuns</th>
                                    <th>Nome Sim</th>
                                    <th>Nome Fantasia</th>
                                    <th>Detalhe</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;

                    // Iterar sobre cada item nos dados do "Alvo"
                    data.forEach(function(item) {
                        let iconSocio = "";
                        let tooltipText = "";
                        let tdClass = "";  // Classe CSS do <td>

                        if (item.tp_socio === 0) {
                            iconSocio = '<i class="fas fa-unlock text-danger"></i>';  // Cadeado aberto → PJs não sócias
                            tooltipText = "PJs não sócias";
                            tdClass = "text-danger"; 
                        } else if (item.tp_socio === 1) {
                            iconSocio = '<i class="fas fa-lock text-success"></i>';  // Cadeado fechado → PJs sócias
                            tooltipText = "PJs sócias";
                            tdClass = "";  // Mantém padrão
                        } else if (item.tp_socio === 2) {
                            iconSocio = '<i class="fas fa-equals text-primary"></i>';  // Apenas o símbolo de igualdade;
                            tooltipText = "Mesma PJ";
                            tdClass = "text-muted";  // Texto cinza
                        }

                        tableHTML += `
                            <tr>
                                <td class="${tdClass}" title="${tooltipText}">${iconSocio} ${formatarCNPJ(item.id)}</td>
                                <td class="text-center">${item.cep ? "✔️" : "❌"}</td>
                                <td class="text-center">${item.logradouro ? "✔️" : "❌"}</td>
                                <td class="text-center">${item.cpfResponsavel ? "✔️" : "❌"}</td>
                                <td class="text-center">${item.telefone1 ? "✔️" : "❌"}</td>
                                <td class="text-center">${item.email ? "✔️" : "❌"}</td>
                                <td class="text-center">${item.cnae ? "✔️" : "❌"}</td>
                                <td class="text-center">${item.scomum ? "✔️" : "❌"}</td>
                                <td>${item.nomeSim}</td>
                                <td>${item.nomeFantasia}</td>
                                <td>
                                    <button class="btn btn-secondary btn-sm" title="Detalhes" onclick="abrirTR('tabela_${item.id_alvo}_${item.id}', 'socios_${item.id_alvo}_${item.id}', this, '${token}')">&#9660;</button>
                                </td>
                            </tr>
                            <tr id="tabela_${item.id_alvo}_${item.id}" style="display: none;"></tr>
                            <tr id="socios_${item.id_alvo}_${item.id}" style="display: none;"></tr>
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

                // Agora que os dados foram montados, escondemos o loading
                $("#loading").hide();
                $("#consulta, #sair").prop("disabled", false);
            },
            error: function(xhr, status, error) {
                 // Esconde o loading e reativa os botões ao detectar erro
                $("#loading").hide();
                $("#consulta, #sair").prop("disabled", false);
                try {
                    const response_parsed = JSON.parse(xhr.responseText);
                    $("#error-message-consulta").addClass("alert-danger").text(response_parsed.error).show();
                } catch (e) {
                    $("#error-message-consulta").addClass("alert-danger").text("Erro desconhecido ao processar a requisição.").show();
                }
            }
        });
        return false;
    });
});

// Função abrir TR de comparacao
function abrirTR(trId, trSociosId, button, token) {
    const trElement = document.getElementById(trId);
    const sociosTrElement = document.getElementById(trSociosId);

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
                addRow("CNAE Fiscal", dadosEs.cnaeFiscal.registro1, dadosEs.cnaeFiscal.registro2);
                
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

                 // Atualizar os sócios comuns na tabela "socios-comuns"
                 const sociosComuns = response.socios_comuns;
                 let sociosTableContent = `
                     <td colspan="100%">
                     <table class="table table-sm">
                        <caption style="caption-side: top;">
                            <strong>Sócios compartilhados entre as empresas ${formatarCNPJ(ids[0])} e ${formatarCNPJ(ids[1])}</strong>
                        </caption>
                        <thead>
                            <tr>
                                <th>Código da Pessoa</th>
                                <th>Tipo da Pessoa</th>
                            </tr>
                        </thead>
                        <tbody>
                 `;
                 if (sociosComuns.length > 0) {
                    sociosComuns.forEach(socio => {
                        let codigoPessoa = socio.socios;
                        let tipoPessoa = socio.tp_socio === "1" ? "Pessoa Jurídica" : "Pessoa Física";

                        // Formatar CNPJ ou CPF corretamente
                        if (socio.tp_socio === "1") {
                            codigoPessoa = formatarCNPJ(codigoPessoa);
                        } else {
                            codigoPessoa = formatarCPF(codigoPessoa);
                        }

                        sociosTableContent += `
                            <tr>
                                <td>${codigoPessoa}</td>
                                <td>${tipoPessoa}</td>
                            </tr>
                        `;
                    });

                    sociosTableContent += `</tbody></table><td>`;

                    sociosTrElement.innerHTML = sociosTableContent;
                    $(sociosTrElement).show();  // Exibe o <tr>
                }
            },
            error: function(xhr, status, error) {
                const response_parsed = JSON.parse(xhr.responseText);
                alert("Erro ao buscar a comparação: " + response_parsed.error);
            }
        });
    }

    // Exibe o trElement
    trElement.style.display = 'table-row';
    sociosTrElement.style.display = 'table-row';
    // Altera o botão para mostrar a seta para cima
    button.innerHTML = '&#9650;'; // Seta para cima
    // Altera a função onclick para fechar o TR
    button.setAttribute('onclick', `fecharTR('${trId}', '${trSociosId}', this, '${token}')`);
}
    
// Função para fechar o div e alterar a seta
function fecharTR(trId, trSociosId, button, token) {
    var trElement = document.getElementById(trId);
    var sociosTrElement = document.getElementById(trSociosId);

    // Oculta o TR de detalhes
    trElement.style.display = 'none';

    // Oculta a linha dos sócios em comum
    sociosTrElement.style.display = 'none';    
    
    // Altera o botão para mostrar a seta para baixo
    button.innerHTML = '&#9660;'; // Seta para baixo
    
    // Altera a função onclick para abrir o div novamente
    button.setAttribute('onclick', `abrirTR('${trId}', '${trSociosId}', this, '${token}')`);
}

function formatarCPF(cpfRaw) {
    // Remover qualquer caractere que não seja número
    cpfRaw = cpfRaw.replace(/\D/g, '');

    // Se exceder 11 dígitos, pegar apenas os últimos 11
    if (cpfRaw.length > 11) {
        cpfRaw = cpfRaw.slice(-11);
    }

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

function formatarTextoAlvo(texto) {
    // Expressão regular para capturar o número de 8 dígitos e qualquer texto após o hífen
    const regex = /^Alvo = (\d{8}) - (.*)$/;
    const match = texto.match(regex);

    if (match) {
        const cnpjBase = match[1]; // Captura o número de 8 dígitos
        const textoAposHifen = match[2]; // Captura o texto após o hífen
        const cnpjFormatado = formatarCNPJ(cnpjBase); // Formata o CNPJ
        return `Alvo = ${cnpjFormatado} - ${textoAposHifen}`; // Retorna a string formatada
    } else {
        return texto; // Retorna o texto original se não corresponder ao padrão esperado
    }
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

function limparMensagensTela() {
    // Esconder mensagens de erro e alerta
    $("#error-message").hide().text("");
    $("#error-message-consulta").hide().text("");
    $("#alert-message").hide().text("");
}

function esvaziarTabelas(){
    // Limpa o contêiner de tabelas antes de renderizar novas tabelas
    $("#tabelas-container").empty();
}

function toggleLike() {
    let likeIcon = document.getElementById("like-icon");
    let dislikeIcon = document.getElementById("dislike-icon");
    let cnpjs = document.getElementById("lista_cnpjs").value; // Captura os CNPJs digitados

    let acao = likeIcon.classList.contains("far") ? "Like" : "Like Removido";

    // Alterna o ícone de like
    likeIcon.classList.toggle("far");
    likeIcon.classList.toggle("fas");
    likeIcon.style.color = likeIcon.classList.contains("fas") ? "#198754" : "";

    // Desativa o dislike se ativado
    if (dislikeIcon.classList.contains("fas")) {
        dislikeIcon.classList.remove("fas");
        dislikeIcon.classList.add("far");
        dislikeIcon.style.color = "";
    }

    // Enviar ação ao servidor
    enviarLogParaServidor(acao, cnpjs);
}

function toggleDislike() {
    let likeIcon = document.getElementById("like-icon");
    let dislikeIcon = document.getElementById("dislike-icon");
    let cnpjs = document.getElementById("lista_cnpjs").value; // Captura os CNPJs digitados

    let acao = dislikeIcon.classList.contains("far") ? "Dislike" : "Dislike Removido";

    // Alterna o ícone de dislike
    dislikeIcon.classList.toggle("far");
    dislikeIcon.classList.toggle("fas");
    dislikeIcon.style.color = dislikeIcon.classList.contains("fas") ? "#dc3545" : "";

    // Desativa o like se ativado
    if (likeIcon.classList.contains("fas")) {
        likeIcon.classList.remove("fas");
        likeIcon.classList.add("far");
        likeIcon.style.color = "";
    }

    // Enviar ação ao servidor
    enviarLogParaServidor(acao, cnpjs);
}

function enviarLogParaServidor(acao, cnpjs) {
    $.ajax({
        type: "POST",
        url: "/log_acao",  // Nova rota no servidor
        data: JSON.stringify({ acao: acao, cnpjs: cnpjs }),
        contentType: "application/json",
        success: function(response) {
            console.log("Log enviado ao servidor:", response);
        },
        error: function(xhr, status, error) {
            console.error("Erro ao enviar log para o servidor:", error);
        }
    });
}

