class TourMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_template_response(self, request, response):
        if hasattr(response, 'context_data') and response.context_data is not None:
            tour_step = request.session.pop('tour_step', '')
            show_tour = tour_step in ('dashboard', 'prompt') or request.GET.get('tour') == 'true'
            response.context_data['tour_step'] = tour_step
            response.context_data['show_tour'] = show_tour
        return response