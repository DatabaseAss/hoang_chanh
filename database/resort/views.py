from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Customer, Package, Roomtype, Receipt, Branch, Bedinfo, SupplyInRoom
from django.contrib import messages
from django.db import connection
from .const import MONTH
# Create your views here.
def home(request):
    return redirect('/branch/1')

@login_required(login_url='/login')
def dashboard(request, branch):

    #   DO STATS
    print(branch)
    cursor =  connection.cursor()
    default_total_guest = [0 for _ in range(12)]
    percentages = [0 for _ in range(12)]
    SCALE = 200

    if request.method == 'GET':
        year = request.GET.get('year')

    if not year:
        year = 2022
    
    FUNCTION = "SELECT * FROM f_TotalGuest({}, {})".format(branch, year)
    # answer = (str(branch), str(year))
    cursor.execute(FUNCTION)
    querySet = cursor.fetchall()
    if not len(querySet) == 0:
        for result in querySet:
            print(result[1])
            default_total_guest[result[0] -1] = result[1]

        for idx, item in enumerate(default_total_guest):
            percentages[idx] = int((item / sum(default_total_guest))*SCALE)

    stats = dict()
    for idx, month in enumerate(MONTH):
        stats[idx] = [percentages[idx], default_total_guest[idx], MONTH[idx]]
    

    total_customer = Customer.objects.count()
    total_package = Package.objects.count()

    #   GET all branches
    num_branch = 0
    for _, _ in enumerate(Branch.objects.all()):
        num_branch += 1
    branches_link = ["/branch/" + str(x) for x in range(1,num_branch)]
    #   GET all branches
    
    if request.method == 'GET':

        search_key = request.GET.get("search_key")
        
        if search_key:
            customers = Customer.objects.order_by('id').all().filter(fullname__icontains=search_key)
        else:
            customers = Customer.objects.order_by('id').all()

        receipts = Receipt.objects.all().filter(receipt_customerid__in = customers)
        for item in receipts:
            print(item.receipt_customerid.fullname)
    return render(request, 'dashboard.html', context={
        'customers': customers,
        'receipts': receipts,
        'total_customers':  total_customer,
        'total_package': total_package,
        'branches': branches_link,
        'branch': branch,
        'stats': stats.values()
    })

def room(request):

    return render(request, 'room.html')

def roomtype(request):
    
    roomtypes = Roomtype.objects.all()
    if request.method == 'GET':
            search_key = request.GET.get('search_roomtype')
            if search_key:
                print(search_key)
                roomtypes = Roomtype.objects.all().filter(typename__icontains = search_key)
                
    return render(request, 'roomtype.html', context = {
        'room_types': roomtypes
    })

def addroom(request):
    if request.method == "POST":

        room_type_area = request.POST['area']
        room_type_des = request.POST['description']
        room_type_cap = request.POST['capacity']
        room_type_name = request.POST['roomtypename']
        try:
            new_room_type = Roomtype.objects.create(
                typename = room_type_name,
                area = float(room_type_area),
                capacity = room_type_cap,
                descriptions = room_type_des
            )
            new_room_type.save()
        except:
            messages.info(request, 'Some information of room type provided is incorrect! Please check again')
            return redirect('/addroom')

        ##  Add bed information
        try:
            bed_size = [float(bedsize) for bedsize in  request.POST.getlist('bedsize')]
            bed_quantity = [int(bedquantity) for bedquantity in request.POST.getlist('bedquantity')]
        except:
            messages.info(request, 'Value error. Maybe you enter wrong format: Float: x.x not x,x')
            return redirect('/addroom')

        if len(bed_size) != len(set(bed_size)):
            messages.info(request, "Same bed size need to be defined in Bed quantity")
            return redirect('/addroom')

        try: 
            for idx, _size in enumerate(bed_size):
                Bedinfo.objects.create(
                    bed_typeid = new_room_type,
                    size = _size,
                    quantity = bed_quantity[idx]
                )
        except:
            messages.info(request, "Some errors occure in adding bed information. Please try again")
            return redirect('/addroom')

        ##  Check supply information
        try:
            supply_id_list = [int(supply_id) for supply_id in  request.POST.getlist('supply_id')]
            supply_quantity = [int(_quantity) for _quantity in request.POST.getlist('supply_quantity')]
        except:
            messages.info(request, 'Value error. Maybe you enter wrong format: Supply ID: Int & Quantity: Int')
            return redirect('/addroom')

        if len(supply_id_list) != len(set(supply_id_list)):
            messages.info(request, "Same supply id need to be defined in Supply quantity")
            return redirect('/addroom')
        try:
            for idx, sid in enumerate(supply_id_list):
                SupplyInRoom.objects.create (
                    sir_supplyid = sid,
                    sir_typeid = new_room_type,
                    num_supply = supply_quantity[idx]
                )
        except:
            messages.info(request, "Some errors occur in adding supply. Please try again")
            return redirect('/addroom')
        
        messages.info(request, "Create successfully")
    return render(request, 'addroom.html')