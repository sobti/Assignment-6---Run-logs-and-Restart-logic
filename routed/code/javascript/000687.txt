(function ($) {
    $("#frm_agregar_rol").submit(function (ev) {
        ev.preventDefault();
        $.ajax({
            url: 'Roles/agregarRoles',
            type: 'POST',
            data: $(this).serialize(),
            success: function (data, xhr) {
                document.getElementById('ROLE_name_alerta').style.display = 'none';
                document.getElementById('ROLE_shortname_alerta').style.display = 'none';
                document.getElementById('ROLE_description_alerta').style.display = 'none';
                $("#sample_1").DataTable().ajax.reload();
                $('#agregar').removeClass('fade-in');
                $('#agregar').addClass('fade');
                document.getElementById('agregar').style.display = 'none';
                document.getElementById('alerta_principal').style.display = 'inherit';
                $("#frm_agregar_rol")[0].reset();
            },
            error: function (xhr) {
                document.getElementById('ROLE_name_alerta').style.display = 'none';
                document.getElementById('ROLE_shortname_alerta').style.display = 'none';
                document.getElementById('ROLE_description_alerta').style.display = 'none';
                if (xhr.status == 402) {
                    var json = JSON.parse(xhr.responseText);
                    
                    if (json.ROLE_name.length != 0) {
                        $("#ROLE_name_alerta > div").html(json.ROLE_name);
                        document.getElementById('ROLE_name_alerta').style.display = 'inherit';
                    }
                    if (json.ROLE_shortname.length != 0) {
                        $("#ROLE_shortname_alerta > div").html(json.ROLE_shortname);
                        document.getElementById('ROLE_shortname_alerta').style.display = 'inherit';
                    }
                    if (json.ROLE_description.length != 0) {
                        $("#ROLE_description_alerta > div").html(json.ROLE_description);
                        document.getElementById('ROLE_description_alerta').style.display = 'inherit';
                    }
                } else if (xhr.status == 401) {
                    document.getElementById('alerta').style.display = 'inherit';
                }
            },

        });
    });
})(jQuery)
