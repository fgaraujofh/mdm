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
            }
        });
        return false;
    });
});
