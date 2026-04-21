from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'grand_hotel_secret_key_2026'   # Change this in production!

# ─── Helpers ────────────────────────────────────────────────────────────────

def login_required(f):
    """Redirect unauthenticated users to /login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'role' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """Allow only Admin role; redirect others."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'Admin':
            flash('You do not have permission to view that page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Root redirect — send everyone to /login."""
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Already logged in? Send to the right dashboard.
    if 'role' in session:
        if session['role'] == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('staff_dashboard'))

    if request.method == 'POST':
        role     = request.form.get('role', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # ── Admin login (hardcoded credentials) ──
        if role == 'Admin':
            if username == 'admin' and password == 'admin123':
                session['role']     = 'Admin'
                session['username'] = 'Admin'
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials. Please try again.', 'error')
                return render_template('login.html')

        # ── Staff login (database lookup) ──
        elif role == 'Staff':
            if password != 'staff123':
                flash('Invalid staff credentials. Please try again.', 'error')
                return render_template('login.html')

            try:
                conn   = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                # Adjust the column names below to match your actual Staff table schema
                cursor.execute(
                    "SELECT * FROM Staff WHERE StaffID = %s",
                    (username,)
                )
                staff = cursor.fetchone()
                cursor.close()
                conn.close()

                if staff:
                    session['role']     = 'Staff'
                    session['username'] = username
                    session['staff_id'] = staff['StaffID']
                    return redirect(url_for('staff_dashboard'))
                else:
                    flash('Staff ID not found in the database.', 'error')
                    return render_template('login.html')

            except Exception as e:
                flash(f'Database error during login: {e}', 'error')
                return render_template('login.html')

        else:
            flash('Please select a valid role.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Guests")
    total_guests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Rooms")
    total_rooms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Staff")
    total_staff = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        total_guests=total_guests,
        total_rooms=total_rooms,
        total_staff=total_staff
    )


@app.route('/staff_dashboard')
@login_required
def staff_dashboard():
    if session.get('role') not in ('Admin', 'Staff'):
        flash('Access denied.', 'error')
        return redirect(url_for('login'))

    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Guests")
    total_guests = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Rooms WHERE Status = 'Available'")
    available_rooms = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        'staff_dashboard.html',
        total_guests=total_guests,
        available_rooms=available_rooms
    )


# ─── Guests ─────────────────────────────────────────────────────────────────

@app.route('/guests')
@login_required
def guests():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT GuestID, FirstName, LastName, Email, Phone FROM Guests")
    guests_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('guests.html', guests=guests_list)


@app.route('/add_guest', methods=['GET', 'POST'])
@login_required
def add_guest():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name',  '').strip()
        email      = request.form.get('email',      '').strip()
        phone      = request.form.get('phone',      '').strip()
        address    = request.form.get('address',    '').strip()

        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Guests (FirstName, LastName, Email, Phone, Address) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, email, phone, address)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Guest added successfully!', 'success')
            return redirect(url_for('guests'))
        except Exception as e:
            flash(f'Error adding guest: {e}', 'error')

    return render_template('add_guest.html')


@app.route('/edit_guest/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_guest(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name',  '').strip()
        email      = request.form.get('email',      '').strip()
        phone      = request.form.get('phone',      '').strip()
        address    = request.form.get('address',    '').strip()
        try:
            cursor.execute(
                """UPDATE Guests
                   SET FirstName=%s, LastName=%s, Email=%s, Phone=%s, Address=%s
                   WHERE GuestID=%s""",
                (first_name, last_name, email, phone, address, id)
            )
            conn.commit()
            flash('Guest updated successfully!', 'success')
            return redirect(url_for('guests'))
        except Exception as e:
            flash(f'Error updating guest: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

    # GET — fetch the current record
    cursor.execute(
        "SELECT GuestID, FirstName, LastName, Email, Phone, Address FROM Guests WHERE GuestID = %s", (id,)
    )
    guest = cursor.fetchone()
    cursor.close()
    conn.close()
    if not guest:
        flash('Guest not found.', 'error')
        return redirect(url_for('guests'))
    return render_template('edit_guest.html', guest=guest)


@app.route('/delete_guest/<int:id>')
@login_required
def delete_guest(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Guests WHERE GuestID = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Guest deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting guest: {e}', 'error')
    return redirect(url_for('guests'))


# ─── Rooms ───────────────────────────────────────────────────────────────────

@app.route('/rooms')
@login_required
def rooms():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.RoomID, r.RoomNumber, r.Floor, r.Status,
               rc.CategoryName
        FROM   Rooms r
        JOIN   RoomCategories rc ON r.CategoryID = rc.CategoryID
        ORDER  BY r.RoomNumber
    """)
    rooms_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('rooms.html', rooms=rooms_list)


@app.route('/add_room', methods=['GET', 'POST'])
@login_required
@admin_required
def add_room():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        room_number = request.form.get('room_number', '').strip()
        floor       = request.form.get('floor',       '').strip()
        category_id = request.form.get('category_id', '').strip()
        status      = request.form.get('status',      'Available').strip()

        try:
            cursor.execute(
                "INSERT INTO Rooms (RoomNumber, Floor, CategoryID, Status) VALUES (%s, %s, %s, %s)",
                (room_number, floor, category_id, status)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Room added successfully!', 'success')
            return redirect(url_for('rooms'))
        except Exception as e:
            flash(f'Error adding room: {e}', 'error')

    cursor.execute("SELECT CategoryID, CategoryName FROM RoomCategories ORDER BY CategoryName")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_room.html', categories=categories)


@app.route('/edit_room/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_room(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        room_number = request.form.get('room_number', '').strip()
        floor       = request.form.get('floor',       '').strip()
        category_id = request.form.get('category_id', '').strip()
        status      = request.form.get('status',      'Available').strip()
        try:
            cursor.execute(
                """UPDATE Rooms SET RoomNumber=%s, Floor=%s, CategoryID=%s, Status=%s
                   WHERE RoomID=%s""",
                (room_number, floor, category_id, status, id)
            )
            conn.commit()
            flash('Room updated successfully!', 'success')
            return redirect(url_for('rooms'))
        except Exception as e:
            flash(f'Error updating room: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

    cursor.execute(
        """SELECT r.RoomID, r.RoomNumber, r.Floor, r.Status, r.CategoryID
           FROM Rooms r WHERE r.RoomID = %s""", (id,)
    )
    room = cursor.fetchone()
    cursor.execute("SELECT CategoryID, CategoryName FROM RoomCategories ORDER BY CategoryName")
    categories = cursor.fetchall()
    cursor.close()
    conn.close()
    if not room:
        flash('Room not found.', 'error')
        return redirect(url_for('rooms'))
    return render_template('edit_room.html', room=room, categories=categories)


@app.route('/delete_room/<int:id>')
@login_required
@admin_required
def delete_room(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Rooms WHERE RoomID = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Room deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting room: {e}', 'error')
    return redirect(url_for('rooms'))


# ─── Reservations ─────────────────────────────────────────────────────────────

@app.route('/reservations')
@login_required
def reservations():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT res.ReservationID,
               res.CheckInDate,
               res.CheckOutDate,
               res.BookingStatus,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
               r.RoomNumber,
               IFNULL(s.FirstName, 'Unassigned') AS StaffName
        FROM   Reservations res
        JOIN   Guests g   ON res.GuestID  = g.GuestID
        JOIN   Rooms  r   ON res.RoomID   = r.RoomID
        LEFT JOIN Staff  s   ON res.AssignedStaffID  = s.StaffID
        ORDER  BY res.ReservationID DESC
    """)
    reservations_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('reservations.html', reservations=reservations_list)


@app.route('/add_reservation', methods=['GET', 'POST'])
@login_required
def add_reservation():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        guest_id           = request.form.get('guest_id')
        room_id            = request.form.get('room_id')
        assigned_staff_id  = request.form.get('assigned_staff_id') or None
        check_in           = request.form.get('check_in')
        check_out          = request.form.get('check_out')
        booking_status     = request.form.get('booking_status', 'Confirmed').strip()

        try:
            cursor.execute(
                """
                INSERT INTO Reservations
                    (GuestID, RoomID, AssignedStaffID, CheckInDate, CheckOutDate, BookingStatus)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (guest_id, room_id, assigned_staff_id, check_in, check_out, booking_status)
            )
            # If checking in immediately, mark the room as Occupied
            if booking_status == 'Checked-In':
                cursor.execute(
                    "UPDATE Rooms SET Status = 'Occupied' WHERE RoomID = %s",
                    (room_id,)
                )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Reservation added successfully!', 'success')
            return redirect(url_for('reservations'))
        except Exception as e:
            flash(f'Error adding reservation: {e}', 'error')

    # GET — populate dropdowns from live DB data
    cursor.execute("SELECT GuestID, FirstName, LastName FROM Guests ORDER BY FirstName")
    guests_list = cursor.fetchall()

    cursor.execute("SELECT RoomID, RoomNumber, Floor FROM Rooms WHERE Status = 'Available' ORDER BY RoomNumber")
    available_rooms = cursor.fetchall()

    cursor.execute("SELECT StaffID, FirstName, LastName FROM Staff ORDER BY FirstName")
    staff_list = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(
        'add_reservation.html',
        guests=guests_list,
        rooms=available_rooms,
        staff=staff_list
    )


@app.route('/edit_reservation/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_reservation(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        guest_id          = request.form.get('guest_id')
        room_id           = request.form.get('room_id')
        assigned_staff_id = request.form.get('assigned_staff_id') or None
        check_in          = request.form.get('check_in')
        check_out         = request.form.get('check_out')
        booking_status    = request.form.get('booking_status', 'Confirmed').strip()
        try:
            # Fetch old room/status before update
            cursor.execute(
                "SELECT RoomID, BookingStatus FROM Reservations WHERE ReservationID=%s", (id,)
            )
            old = cursor.fetchone()
            cursor.execute(
                """UPDATE Reservations
                   SET GuestID=%s, RoomID=%s, AssignedStaffID=%s,
                       CheckInDate=%s, CheckOutDate=%s, BookingStatus=%s
                   WHERE ReservationID=%s""",
                (guest_id, room_id, assigned_staff_id,
                 check_in, check_out, booking_status, id)
            )
            # Sync room status
            if booking_status == 'Checked-In':
                cursor.execute("UPDATE Rooms SET Status='Occupied' WHERE RoomID=%s", (room_id,))
                if old and old['RoomID'] != int(room_id):
                    cursor.execute("UPDATE Rooms SET Status='Available' WHERE RoomID=%s", (old['RoomID'],))
            elif booking_status in ('Checked-Out', 'Cancelled'):
                cursor.execute("UPDATE Rooms SET Status='Available' WHERE RoomID=%s", (room_id,))
                if old and old['RoomID'] != int(room_id):
                    cursor.execute("UPDATE Rooms SET Status='Available' WHERE RoomID=%s", (old['RoomID'],))
            elif old and old['BookingStatus'] == 'Checked-In' and booking_status != 'Checked-In':
                cursor.execute("UPDATE Rooms SET Status='Available' WHERE RoomID=%s", (old['RoomID'],))
            conn.commit()
            flash('Reservation updated successfully!', 'success')
            return redirect(url_for('reservations'))
        except Exception as e:
            flash(f'Error updating reservation: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT ReservationID, GuestID, RoomID, AssignedStaffID,
               CheckInDate, CheckOutDate, BookingStatus
        FROM   Reservations WHERE ReservationID = %s
    """, (id,))
    res = cursor.fetchone()
    if not res:
        flash('Reservation not found.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('reservations'))

    cursor.execute("SELECT GuestID, FirstName, LastName FROM Guests ORDER BY FirstName")
    guests_list = cursor.fetchall()
    cursor.execute("SELECT RoomID, RoomNumber, Floor, Status FROM Rooms ORDER BY RoomNumber")
    rooms_list = cursor.fetchall()
    cursor.execute("SELECT StaffID, FirstName, LastName FROM Staff ORDER BY FirstName")
    staff_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template(
        'edit_reservation.html',
        res=res,
        guests=guests_list,
        rooms=rooms_list,
        staff=staff_list
    )


@app.route('/delete_reservation/<int:id>')
@login_required
def delete_reservation(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch room & status so we can free the room if it was Checked-In
        cursor.execute(
            "SELECT RoomID, BookingStatus FROM Reservations WHERE ReservationID=%s", (id,)
        )
        res = cursor.fetchone()
        if res:
            cursor.execute(
                "UPDATE Rooms SET Status='Available' WHERE RoomID=%s", (res['RoomID'],)
            )
        cursor.execute("DELETE FROM ServiceCharges WHERE ReservationID = %s", (id,))
        cursor.execute("DELETE FROM Invoices WHERE ReservationID = %s", (id,))
        cursor.execute("DELETE FROM Reservations WHERE ReservationID=%s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Reservation deleted and room freed.', 'success')
    except Exception as e:
        flash(f'Error deleting reservation: {e}', 'error')
    return redirect(url_for('reservations'))


# ─── Services ────────────────────────────────────────────────────────────────

@app.route('/services')
@login_required
def services():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT ServiceID, ServiceName, BasePrice, Description FROM Services ORDER BY ServiceName")
    services_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('services.html', services=services_list)


@app.route('/add_service', methods=['GET', 'POST'])
@login_required
@admin_required
def add_service():
    if request.method == 'POST':
        service_name = request.form.get('service_name', '').strip()
        base_price   = request.form.get('base_price',   '').strip()
        description  = request.form.get('description',  '').strip()

        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Services (ServiceName, BasePrice, Description) VALUES (%s, %s, %s)",
                (service_name, base_price, description)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Service added successfully!', 'success')
            return redirect(url_for('services'))
        except Exception as e:
            flash(f'Error adding service: {e}', 'error')

    return render_template('add_service.html')


@app.route('/edit_service/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_service(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        service_name = request.form.get('service_name', '').strip()
        base_price   = request.form.get('base_price',   '').strip()
        description  = request.form.get('description',  '').strip()
        try:
            cursor.execute(
                """UPDATE Services SET ServiceName=%s, BasePrice=%s, Description=%s
                   WHERE ServiceID=%s""",
                (service_name, base_price, description, id)
            )
            conn.commit()
            flash('Service updated successfully!', 'success')
            return redirect(url_for('services'))
        except Exception as e:
            flash(f'Error updating service: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

    cursor.execute(
        "SELECT ServiceID, ServiceName, BasePrice, Description FROM Services WHERE ServiceID = %s", (id,)
    )
    service = cursor.fetchone()
    cursor.close()
    conn.close()
    if not service:
        flash('Service not found.', 'error')
        return redirect(url_for('services'))
    return render_template('edit_service.html', service=service)


@app.route('/delete_service/<int:id>')
@login_required
@admin_required
def delete_service(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Services WHERE ServiceID = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Service deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting service: {e}', 'error')
    return redirect(url_for('services'))


# ─── Service Charges (Billing) ───────────────────────────────────────────────

@app.route('/service_charges')
@login_required
def service_charges():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT sc.ChargeID,
               sc.DateOrdered,
               sc.Quantity,
               sc.TotalCharge,
               sv.ServiceName,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName
        FROM   ServiceCharges sc
        JOIN   Services      sv   ON sc.ServiceID      = sv.ServiceID
        JOIN   Reservations  res  ON sc.ReservationID  = res.ReservationID
        JOIN   Guests        g    ON res.GuestID        = g.GuestID
        ORDER  BY sc.DateOrdered DESC
    """)
    charges_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('service_charges.html', charges=charges_list)


@app.route('/add_service_charge', methods=['GET', 'POST'])
@login_required
def add_service_charge():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')
        service_id     = request.form.get('service_id')
        quantity       = request.form.get('quantity', 1)

        try:
            # Step 1: Look up BasePrice from Services table
            cursor.execute("SELECT BasePrice FROM Services WHERE ServiceID = %s", (service_id,))
            service = cursor.fetchone()
            if not service:
                flash('Selected service not found.', 'error')
                return redirect(url_for('add_service_charge'))

            base_price   = float(service['BasePrice'])
            total_charge = base_price * int(quantity)

            # Step 2: Insert the charge with calculated total and current datetime
            cursor.execute(
                """
                INSERT INTO ServiceCharges (ReservationID, ServiceID, Quantity, TotalCharge, DateOrdered)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (reservation_id, service_id, quantity, total_charge)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash(f'Service charge of ₹{total_charge:,.2f} added successfully!', 'success')
            return redirect(url_for('service_charges'))
        except Exception as e:
            flash(f'Error adding charge: {e}', 'error')

    # GET — populate both dropdowns from live DB
    cursor.execute("""
        SELECT res.ReservationID,
               res.BookingStatus,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
               r.RoomNumber
        FROM   Reservations res
        JOIN   Guests g ON res.GuestID = g.GuestID
        JOIN   Rooms  r ON res.RoomID  = r.RoomID
        WHERE  res.BookingStatus IN ('Confirmed', 'Checked-In')
        ORDER  BY g.FirstName
    """)
    active_reservations = cursor.fetchall()

    cursor.execute("SELECT ServiceID, ServiceName, BasePrice FROM Services ORDER BY ServiceName")
    services_list = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(
        'add_service_charge.html',
        reservations=active_reservations,
        services=services_list
    )


@app.route('/edit_service_charge/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_service_charge(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        quantity   = request.form.get('quantity', 1)
        service_id = request.form.get('service_id')
        try:
            cursor.execute("SELECT BasePrice FROM Services WHERE ServiceID = %s", (service_id,))
            svc = cursor.fetchone()
            if not svc:
                flash('Service not found.', 'error')
                return redirect(url_for('service_charges'))
            total_charge = float(svc['BasePrice']) * int(quantity)
            cursor.execute(
                """UPDATE ServiceCharges
                   SET ServiceID=%s, Quantity=%s, TotalCharge=%s
                   WHERE ChargeID=%s""",
                (service_id, quantity, total_charge, id)
            )
            conn.commit()
            flash('Charge updated successfully!', 'success')
            return redirect(url_for('service_charges'))
        except Exception as e:
            flash(f'Error updating charge: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

    cursor.execute("""
        SELECT sc.ChargeID, sc.ReservationID, sc.ServiceID, sc.Quantity, sc.TotalCharge,
               sc.DateOrdered,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
               r.RoomNumber
        FROM   ServiceCharges sc
        JOIN   Reservations   res ON sc.ReservationID = res.ReservationID
        JOIN   Guests         g   ON res.GuestID      = g.GuestID
        JOIN   Rooms          r   ON res.RoomID       = r.RoomID
        WHERE  sc.ChargeID = %s
    """, (id,))
    charge = cursor.fetchone()
    cursor.execute("SELECT ServiceID, ServiceName, BasePrice FROM Services ORDER BY ServiceName")
    services_list = cursor.fetchall()
    cursor.close()
    conn.close()
    if not charge:
        flash('Charge not found.', 'error')
        return redirect(url_for('service_charges'))
    return render_template('edit_service_charge.html', charge=charge, services=services_list)


@app.route('/delete_service_charge/<int:id>')
@login_required
def delete_service_charge(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ServiceCharges WHERE ChargeID = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Service charge deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting charge: {e}', 'error')
    return redirect(url_for('service_charges'))


# ─── Room Categories ─────────────────────────────────────────────────────────

@app.route('/categories')
@login_required
def categories():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT CategoryID, CategoryName, PricePerNight, MaxCapacity FROM RoomCategories ORDER BY CategoryName"
    )
    categories_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('categories.html', categories=categories_list)


@app.route('/add_category', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    if request.method == 'POST':
        category_name  = request.form.get('category_name',  '').strip()
        price_per_night = request.form.get('price_per_night', '').strip()
        max_capacity   = request.form.get('max_capacity',   '').strip()

        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO RoomCategories (CategoryName, PricePerNight, MaxCapacity) VALUES (%s, %s, %s)",
                (category_name, price_per_night, max_capacity)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Room category added successfully!', 'success')
            return redirect(url_for('categories'))
        except Exception as e:
            flash(f'Error adding category: {e}', 'error')

    return render_template('add_category.html')


@app.route('/edit_category/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        category_name   = request.form.get('category_name',   '').strip()
        price_per_night = request.form.get('price_per_night', '').strip()
        max_capacity    = request.form.get('max_capacity',    '').strip()
        try:
            cursor.execute(
                """UPDATE RoomCategories
                   SET CategoryName=%s, PricePerNight=%s, MaxCapacity=%s
                   WHERE CategoryID=%s""",
                (category_name, price_per_night, max_capacity, id)
            )
            conn.commit()
            flash('Category updated successfully!', 'success')
            return redirect(url_for('categories'))
        except Exception as e:
            flash(f'Error updating category: {e}', 'error')
        finally:
            cursor.close()
            conn.close()

    # GET — fetch existing record
    cursor.execute(
        "SELECT CategoryID, CategoryName, PricePerNight, MaxCapacity FROM RoomCategories WHERE CategoryID = %s", (id,)
    )
    category = cursor.fetchone()
    cursor.close()
    conn.close()
    if not category:
        flash('Category not found.', 'error')
        return redirect(url_for('categories'))
    return render_template('edit_category.html', category=category)


@app.route('/delete_category/<int:id>')
@login_required
@admin_required
def delete_category(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM RoomCategories WHERE CategoryID = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Category deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting category: {e}', 'error')
    return redirect(url_for('categories'))


# ─── Staff Management ────────────────────────────────────────────────────────

@app.route('/staff')
@login_required
@admin_required
def staff():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT StaffID, FirstName, LastName, Role, ContactNumber FROM Staff ORDER BY FirstName")
    staff_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('staff.html', staff=staff_list)


@app.route('/add_staff', methods=['GET', 'POST'])
@login_required
@admin_required
def add_staff():
    if request.method == 'POST':
        first_name     = request.form.get('first_name',     '').strip()
        last_name      = request.form.get('last_name',      '').strip()
        role           = request.form.get('role',           '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        try:
            conn   = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Staff (FirstName, LastName, Role, ContactNumber) VALUES (%s, %s, %s, %s)",
                (first_name, last_name, role, contact_number)
            )
            conn.commit()
            cursor.close()
            conn.close()
            flash('Staff member added successfully!', 'success')
            return redirect(url_for('staff'))
        except Exception as e:
            flash(f'Error adding staff: {e}', 'error')
    return render_template('add_staff.html')


@app.route('/edit_staff/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        first_name     = request.form.get('first_name',     '').strip()
        last_name      = request.form.get('last_name',      '').strip()
        role           = request.form.get('role',           '').strip()
        contact_number = request.form.get('contact_number', '').strip()
        try:
            cursor.execute(
                """UPDATE Staff SET FirstName=%s, LastName=%s, Role=%s, ContactNumber=%s
                   WHERE StaffID=%s""",
                (first_name, last_name, role, contact_number, id)
            )
            conn.commit()
            flash('Staff member updated successfully!', 'success')
            return redirect(url_for('staff'))
        except Exception as e:
            flash(f'Error updating staff: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    cursor.execute(
        "SELECT StaffID, FirstName, LastName, Role, ContactNumber FROM Staff WHERE StaffID = %s", (id,)
    )
    member = cursor.fetchone()
    cursor.close()
    conn.close()
    if not member:
        flash('Staff member not found.', 'error')
        return redirect(url_for('staff'))
    return render_template('edit_staff.html', member=member)


@app.route('/delete_staff/<int:id>')
@login_required
@admin_required
def delete_staff(id):
    try:
        conn   = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Staff WHERE StaffID = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Staff member deleted.', 'success')
    except Exception as e:
        flash(f'Error deleting staff: {e}', 'error')
    return redirect(url_for('staff'))


# ─── Checkout & Invoicing ─────────────────────────────────────────────────────

@app.route('/checkout/<int:reservation_id>')
@login_required
def checkout(reservation_id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch reservation with room price and dates
    cursor.execute("""
        SELECT res.ReservationID, res.CheckInDate, res.CheckOutDate,
               res.GuestID, res.RoomID, res.BookingStatus,
               rc.PricePerNight,
               r.RoomNumber,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName
        FROM   Reservations res
        JOIN   Rooms          r  ON res.RoomID   = r.RoomID
        JOIN   RoomCategories rc ON r.CategoryID = rc.CategoryID
        JOIN   Guests         g  ON res.GuestID  = g.GuestID
        WHERE  res.ReservationID = %s
    """, (reservation_id,))
    res = cursor.fetchone()

    if not res:
        flash('Reservation not found.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('reservations'))

    if res['BookingStatus'] != 'Checked-In':
        flash('Only Checked-In reservations can be checked out.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('reservations'))

    # Calculate room cost
    check_in  = res['CheckInDate']
    check_out = res['CheckOutDate']
    from datetime import date
    if isinstance(check_in, str):
        from datetime import datetime
        check_in  = datetime.strptime(check_in,  '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()
    days_stayed  = max((check_out - check_in).days, 1)
    room_cost    = float(res['PricePerNight']) * days_stayed

    # Sum service charges
    cursor.execute(
        "SELECT COALESCE(SUM(TotalCharge), 0) AS ServiceTotal FROM ServiceCharges WHERE ReservationID = %s",
        (reservation_id,)
    )
    svc_row      = cursor.fetchone()
    service_total = svc_row['ServiceTotal'] if svc_row else None
    if service_total is None:
        service_total = 0
    service_cost = float(service_total)

    subtotal   = room_cost + service_cost
    tax        = round(subtotal * 0.10, 2)
    grand_total = round(subtotal + tax, 2)

    try:
        # Insert invoice
        cursor.execute(
            """INSERT INTO Invoices (ReservationID, IssueDate, TotalAmount, Tax, GrandTotal)
               VALUES (%s, CURDATE(), %s, %s, %s)""",
            (reservation_id, subtotal, tax, grand_total)
        )
        invoice_id = cursor.lastrowid

        # Mark reservation as Checked-Out
        cursor.execute(
            "UPDATE Reservations SET BookingStatus='Checked-Out' WHERE ReservationID=%s",
            (reservation_id,)
        )

        # Free up the room
        cursor.execute(
            "UPDATE Rooms SET Status='Available' WHERE RoomID=%s",
            (res['RoomID'],)
        )

        conn.commit()
        cursor.close()
        conn.close()
        flash('Checkout complete! Invoice generated.', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice_id))
    except Exception as e:
        conn.rollback()
        flash(f'Checkout failed: {e}', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('reservations'))


@app.route('/invoices')
@login_required
def invoices():
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT inv.InvoiceID,
               inv.TotalAmount,
               inv.Tax,
               inv.GrandTotal,
               inv.IssueDate,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
               r.RoomNumber,
               res.CheckOutDate
        FROM   Invoices      inv
        JOIN   Reservations  res ON inv.ReservationID = res.ReservationID
        JOIN   Guests        g   ON res.GuestID       = g.GuestID
        JOIN   Rooms         r   ON res.RoomID        = r.RoomID
        ORDER  BY inv.InvoiceID DESC
    """)
    invoices_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('invoices.html', invoices=invoices_list)


@app.route('/view_invoice/<int:invoice_id>')
@login_required
def view_invoice(invoice_id):
    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Full invoice detail
    cursor.execute("""
        SELECT inv.InvoiceID,
               inv.TotalAmount,
               inv.Tax,
               inv.GrandTotal,
               inv.IssueDate,
               res.ReservationID,
               res.CheckInDate,
               res.CheckOutDate,
               res.BookingStatus,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
               g.Email, g.Phone,
               r.RoomNumber, r.Floor,
               rc.CategoryName,
               rc.PricePerNight
        FROM   Invoices      inv
        JOIN   Reservations  res ON inv.ReservationID = res.ReservationID
        JOIN   Guests        g   ON res.GuestID       = g.GuestID
        JOIN   Rooms         r   ON res.RoomID        = r.RoomID
        JOIN   RoomCategories rc ON r.CategoryID      = rc.CategoryID
        WHERE  inv.InvoiceID = %s
    """, (invoice_id,))
    invoice = cursor.fetchone()

    if not invoice:
        flash('Invoice not found.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('invoices'))

    # Itemised service charges
    cursor.execute("""
        SELECT sc.Quantity, sc.TotalCharge, sc.DateOrdered,
               sv.ServiceName, sv.BasePrice
        FROM   ServiceCharges sc
        JOIN   Services       sv ON sc.ServiceID = sv.ServiceID
        WHERE  sc.ReservationID = %s
        ORDER  BY sc.DateOrdered
    """, (invoice['ReservationID'],))
    charges = cursor.fetchall()

    # Days stayed
    from datetime import datetime
    check_in  = invoice['CheckInDate']
    check_out = invoice['CheckOutDate']
    if isinstance(check_in, str):
        check_in  = datetime.strptime(check_in,  '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out, '%Y-%m-%d').date()
    days_stayed = max((check_out - check_in).days, 1)

    cursor.close()
    conn.close()
    return render_template('view_invoice.html',
                           invoice=invoice,
                           charges=charges,
                           days_stayed=days_stayed)


# ─── Staff Profile ───────────────────────────────────────────────────────────

@app.route('/profile')
@login_required
def profile():
    staff_id = session.get('staff_id')
    if not staff_id:
        flash('Profile is only available for Staff accounts.', 'error')
        return redirect(url_for('staff_dashboard'))

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Staff personal details
    cursor.execute(
        "SELECT StaffID, FirstName, LastName, Role, ContactNumber FROM Staff WHERE StaffID = %s",
        (staff_id,)
    )
    staff_member = cursor.fetchone()
    if not staff_member:
        flash('Staff record not found.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('staff_dashboard'))

    # Active reservations assigned to this staff member
    cursor.execute("""
        SELECT res.ReservationID,
               res.CheckInDate,
               res.CheckOutDate,
               res.BookingStatus,
               CONCAT(g.FirstName, ' ', g.LastName) AS GuestName,
               g.Email,
               g.Phone,
               r.RoomNumber
        FROM   Reservations res
        JOIN   Guests g ON res.GuestID = g.GuestID
        JOIN   Rooms  r ON res.RoomID  = r.RoomID
        WHERE  res.AssignedStaffID = %s
          AND  res.BookingStatus IN ('Confirmed', 'Checked-In')
        ORDER  BY res.CheckInDate DESC
    """, (staff_id,))
    assigned_guests = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('profile.html', staff=staff_member, guests=assigned_guests)


if __name__ == '__main__':
    app.run(debug=True)