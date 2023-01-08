from django.urls import path, re_path

from .views import main, system, pdf, api, efiling

urlpatterns = [
    # url(r'^guide$', styleguide.guide),
    path('api/response', api.UserResponseHandler.as_view()),
    path('api/documents/', api.DocumentCreateView.as_view(), name='documents'),
    path('api/documents/<file_key>/<int:rotation>/', api.get_document_file_by_key, name='file_by_key'),

    # we add an extra 'x' to the file extension so the siteminder proxy doesn't treat it as an image
    path('api/documents/<doc_type>/<int:party_code>/<filename>x/<int:size>/', api.DocumentView.as_view(), name='document'),

    path('signin', main.after_login, name="signin"),
    path('logout', main.after_logout, name="logout"),
    path('register', main.register, name="register"),
    path('register_sc', main.register_sc, name="register_sc"),
    path('overview', main.overview, name="overview"),
    path('success', main.success, name="success"),
    path('incomplete', main.incomplete, name="incomplete"),
    path('intercept', main.intercept_page, name="intercept"),
    re_path(r'^dashboard/(?P<nav_step>.*)', main.dashboard_nav, name="dashboard_nav"),
    path('submit/initial', efiling.submit_initial_files, name="submit_initial_files"),
    path('submit/final', efiling.submit_final_files, name="submit_final_files"),
    path('after-submit/initial', efiling.after_submit_initial_files, name="after_submit_initial_files"),
    path('after-submit/final', efiling.after_submit_final_files, name="after_submit_final_files"),
    path('health', system.health),
    path('legal', main.legal, name="legal"),
    path('acknowledgements', main.acknowledgements, name="acknowledgements"),
    path('contact', main.contact, name="contact"),

    # url(r'^headers$', system.headers),

    re_path(r'^pdf-form(?P<form_number>[/bPC/b0-9]{1,3}(_we|_claimant1|_claimant2|_translation|_no_marriage)?)$', pdf.pdf_form, name="pdf_form"),
    path('pdf-images/<doc_type>/<int:party_code>/', pdf.images_to_pdf, name='pdf_images'),
    re_path(r'^prequalification/step_(?P<step>[0-9]{2})$', main.prequalification, name="prequalification"),
    re_path(r'^question/(?P<step>.*)/(?P<sub_step>.*)/$', main.question, name="question_steps"),
    re_path(r'^question/(?P<step>.*)$', main.question, name="question_steps"),
    path('current', system.current, name="current"),
    path('', main.home, name="home"),
]
