"use strict";
{
  const $ = django.jQuery;

  $.fn.djangoCustomSelect2 = function () {
    $.each(this, function (i, element) {
      $(element).select2();
    });
<<<<<<< HEAD
=======

    return this;
  };

  $.fn.djangoAdminSelect2 = function () {
    $.each(this, function (i, element) {
      $(element).select2({
        ajax: {
          data: (params) => {
            return {
              term: params.term,
              page: params.page,
              app_label: element.dataset.appLabel,
              model_name: element.dataset.modelName,
              field_name: element.dataset.fieldName,
            };
          },
        },
      });
    });
>>>>>>> 859fc8d362657ec84aac8b10bb929afbd4ff2a5d
    return this;
  };

  $(function () {
    $(".unfold-admin-autocomplete.admin-autocomplete").djangoCustomSelect2();
<<<<<<< HEAD
=======

    $(".admin-autocomplete")
      .not(".unfold-admin-autocomplete")
      .not("[name*=__prefix__]")
      .djangoAdminSelect2();
  });

  document.addEventListener("formset:added", (event) => {
    $(event.target).find(".admin-autocomplete").djangoAdminSelect2();
>>>>>>> 859fc8d362657ec84aac8b10bb929afbd4ff2a5d
  });
}
