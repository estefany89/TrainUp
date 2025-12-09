from django.shortcuts import render

def descuentos_view(request):
    """
    Vista exclusiva para la sección de descuentos.
    """
    descuentos = [
        {"nombre": "Nike", "logo": "gimnasio/logos/nike.png", "descripcion": "15% de descuento en toda la web de Nike.",
         "codigo": "ROPSK56", "url": "https://www.nike.com"},
        {"nombre": "Adidas", "logo": "gimnasio/logos/adidas.png",
         "descripcion": "10% de descuento en compras mayores a $50.", "codigo": "AD10OFF",
         "url": "https://www.adidas.com"},
        {"nombre": "Puma", "logo": "gimnasio/logos/puma.png",
         "descripcion": "15% de descuento en zapatillas deportivas.", "codigo": "PUMA15",
         "url": "https://www.puma.com"},
        {"nombre": "Reebok", "logo": "gimnasio/logos/reebok.png",
         "descripcion": "20% de descuento en artículos seleccionados.", "codigo": "REE20",
         "url": "https://www.reebok.com"},
        {"nombre": "Decathlon", "logo": "gimnasio/logos/decathlon.png",
         "descripcion": "20% de descuento en equipos deportivos seleccionados.", "codigo": "DEC20",
         "url": "https://www.decathlon.com"},
        {"nombre": "MyProtein", "logo": "gimnasio/logos/myprotein.png",
         "descripcion": "15% de descuento en suplementos deportivos.", "codigo": "MP15",
         "url": "https://www.myprotein.com"},
        {"nombre": "Optimum Nutrition", "logo": "gimnasio/logos/optimum-nutrition.png",
         "descripcion": "10% de descuento en proteínas y suplementos.", "codigo": "ON10",
         "url": "https://www.optimumnutrition.com"},
        {"nombre": "GNC", "logo": "gimnasio/logos/gnc.png", "descripcion": "15% de descuento en todo el sitio web.",
         "codigo": "GNC15", "url": "https://www.gnc.com"},
        {"nombre": "Domino's Pizza", "logo": "gimnasio/logos/domino.png",
         "descripcion": "15% de descuento en pedidos online.", "codigo": "DOM15", "url": "https://www.dominos.com"},
        {"nombre": "Subway", "logo": "gimnasio/logos/subway.png", "descripcion": "10% de descuento en toda la tienda.",
         "codigo": "SUB10", "url": "https://www.subway.com"},
    ]

    return render(request, 'gimnasio/descuentos.html', {'descuentos': descuentos})
