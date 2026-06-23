import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'admin_controller.dart';

class AdminDashboardScreen extends StatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> with SingleTickerProviderStateMixin {
  final AdminController controller = Get.find<AdminController>();
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Console'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout, color: Color(0xFFFF4A75)),
            onPressed: () => controller.authService.logout(),
          )
        ],
        bottom: TabBar(
          controller: _tabController,
          indicatorColor: const Color(0xFF6C63FF),
          tabs: const [
            Tab(icon: Icon(Icons.people_alt), text: 'STUDENTS'),
            Tab(icon: Icon(Icons.co_present), text: 'FACULTY'),
            Tab(icon: Icon(Icons.bluetooth), text: 'BEACONS'),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () => controller.refreshAdminData(),
        color: const Color(0xFF6C63FF),
        child: SafeArea(
          child: Column(
            children: [
              // Analytics Overview Panels
              Padding(
                padding: const EdgeInsets.all(20.0),
                child: _buildAnalyticsHeader(),
              ),

              // Tab views
              Expanded(
                child: TabBarView(
                  controller: _tabController,
                  children: [
                    _buildStudentsTab(),
                    _buildFacultyTab(),
                    _buildBeaconsTab(),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAnalyticsHeader() {
    return Obx(() => GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 3,
      crossAxisSpacing: 10,
      mainAxisSpacing: 10,
      childAspectRatio: 1.5,
      children: [
        _buildStatBox('STUDENTS', '${controller.totalStudents.value}', const Color(0xFF6C63FF)),
        _buildStatBox('FACULTY', '${controller.totalFaculty.value}', const Color(0xFF00D2FF)),
        _buildStatBox('ATTENDANCE', '${controller.attendanceRate.value.toStringAsFixed(1)}%', const Color(0xFF00FF87)),
      ],
    ));
  }

  Widget _buildStatBox(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF161722),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF232533), width: 1),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: TextStyle(color: const Color(0xFF94A3B8).withOpacity(0.8), fontSize: 9, letterSpacing: 0.5)),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(color: color, fontSize: 20, fontWeight: FontWeight.w900),
          ),
        ],
      ),
    );
  }

  Widget _buildStudentsTab() {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF6C63FF),
        onPressed: () => _showAddStudentDialog(),
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: Obx(() {
        if (controller.studentsList.isEmpty) {
          return const Center(child: Text('No students registered.'));
        }
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: controller.studentsList.length,
          itemBuilder: (context, index) {
            final student = controller.studentsList[index];
            return Card(
              child: ListTile(
                leading: const CircleAvatar(child: Icon(Icons.person)),
                title: Text(student['name'] ?? 'John Doe'),
                subtitle: Text('Roll: ${student['roll_no']} • ${student['email']}'),
                trailing: IconButton(
                  icon: const Icon(Icons.delete, color: Color(0xFFFF4A75)),
                  onPressed: () => controller.deleteStudent(student['id']),
                ),
              ),
            );
          },
        );
      }),
    );
  }

  Widget _buildFacultyTab() {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF00D2FF),
        onPressed: () => _showAddFacultyDialog(),
        child: const Icon(Icons.add, color: Colors.white),
      ),
      body: Obx(() {
        if (controller.facultyList.isEmpty) {
          return const Center(child: Text('No faculty registered.'));
        }
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: controller.facultyList.length,
          itemBuilder: (context, index) {
            final fac = controller.facultyList[index];
            return Card(
              child: ListTile(
                leading: const CircleAvatar(child: Icon(Icons.co_present)),
                title: Text(fac['name'] ?? 'Faculty Member'),
                subtitle: Text('Email: ${fac['email']} • Dept: ${fac['department'] ?? 'General'}'),
                trailing: IconButton(
                  icon: const Icon(Icons.delete, color: Color(0xFFFF4A75)),
                  onPressed: () => controller.deleteFaculty(fac['id']),
                ),
              ),
            );
          },
        );
      }),
    );
  }

  Widget _buildBeaconsTab() {
    return Scaffold(
      floatingActionButton: FloatingActionButton(
        backgroundColor: const Color(0xFF00FF87),
        onPressed: () => _showAddBeaconDialog(),
        child: const Icon(Icons.add, color: Colors.black),
      ),
      body: Obx(() {
        if (controller.beaconsList.isEmpty) {
          return const Center(child: Text('No BLE beacons registered.'));
        }
        return ListView.builder(
          padding: const EdgeInsets.all(16),
          itemCount: controller.beaconsList.length,
          itemBuilder: (context, index) {
            final beacon = controller.beaconsList[index];
            return Card(
              child: ListTile(
                leading: const CircleAvatar(child: Icon(Icons.bluetooth)),
                title: Text(beacon['device_name'] ?? 'BLE Beacon'),
                subtitle: Text('UUID: ${beacon['uuid']}\nThreshold: ${beacon['rssi_threshold']} dBm'),
                isThreeLine: true,
                trailing: IconButton(
                  icon: const Icon(Icons.delete, color: Color(0xFFFF4A75)),
                  onPressed: () => controller.deleteBeacon(beacon['id']),
                ),
              ),
            );
          },
        );
      }),
    );
  }

  void _showAddStudentDialog() {
    final nameC = TextEditingController();
    final rollC = TextEditingController();
    final emailC = TextEditingController();
    final deptC = TextEditingController();
    final yearC = TextEditingController();
    final sectC = TextEditingController();

    Get.defaultDialog(
      title: 'Add Student',
      content: SingleChildScrollView(
        child: Column(
          children: [
            TextField(controller: nameC, decoration: const InputDecoration(labelText: 'Name')),
            const SizedBox(height: 8),
            TextField(controller: rollC, decoration: const InputDecoration(labelText: 'Roll No')),
            const SizedBox(height: 8),
            TextField(controller: emailC, decoration: const InputDecoration(labelText: 'Email')),
            const SizedBox(height: 8),
            TextField(controller: deptC, decoration: const InputDecoration(labelText: 'Department')),
            const SizedBox(height: 8),
            TextField(controller: yearC, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Year')),
            const SizedBox(height: 8),
            TextField(controller: sectC, decoration: const InputDecoration(labelText: 'Section')),
          ],
        ),
      ),
      textConfirm: 'ADD',
      textCancel: 'CANCEL',
      confirmTextColor: Colors.white,
      onConfirm: () {
        if (nameC.text.isNotEmpty && rollC.text.isNotEmpty && emailC.text.isNotEmpty) {
          controller.addStudent({
            'name': nameC.text.trim(),
            'roll_no': rollC.text.trim(),
            'email': emailC.text.trim(),
            'department': deptC.text.trim(),
            'year': int.tryParse(yearC.text.trim()) ?? 1,
            'section': sectC.text.trim(),
          });
          Get.back();
        }
      }
    );
  }

  void _showAddFacultyDialog() {
    final nameC = TextEditingController();
    final emailC = TextEditingController();
    final deptC = TextEditingController();

    Get.defaultDialog(
      title: 'Add Faculty',
      content: Column(
        children: [
          TextField(controller: nameC, decoration: const InputDecoration(labelText: 'Name')),
          const SizedBox(height: 8),
          TextField(controller: emailC, decoration: const InputDecoration(labelText: 'Email')),
          const SizedBox(height: 8),
          TextField(controller: deptC, decoration: const InputDecoration(labelText: 'Department')),
        ],
      ),
      textConfirm: 'ADD',
      textCancel: 'CANCEL',
      confirmTextColor: Colors.white,
      onConfirm: () {
        if (nameC.text.isNotEmpty && emailC.text.isNotEmpty) {
          controller.addFaculty({
            'name': nameC.text.trim(),
            'email': emailC.text.trim(),
            'department': deptC.text.trim(),
          });
          Get.back();
        }
      }
    );
  }

  void _showAddBeaconDialog() {
    final classIdC = TextEditingController();
    final nameC = TextEditingController();
    final uuidC = TextEditingController();
    final threshC = TextEditingController();

    Get.defaultDialog(
      title: 'Link BLE Beacon',
      content: Column(
        children: [
          TextField(controller: classIdC, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Classroom ID')),
          const SizedBox(height: 8),
          TextField(controller: nameC, decoration: const InputDecoration(labelText: 'Device Name (e.g. SMARTATTEND_ROOM101)')),
          const SizedBox(height: 8),
          TextField(controller: uuidC, decoration: const InputDecoration(labelText: 'UUID')),
          const SizedBox(height: 8),
          TextField(controller: threshC, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'RSSI Threshold (e.g. -75)')),
        ],
      ),
      textConfirm: 'LINK',
      textCancel: 'CANCEL',
      confirmTextColor: Colors.white,
      onConfirm: () {
        if (classIdC.text.isNotEmpty && nameC.text.isNotEmpty && uuidC.text.isNotEmpty) {
          controller.addBeacon({
            'classroom_id': int.tryParse(classIdC.text.trim()) ?? 1,
            'device_name': nameC.text.trim(),
            'uuid': uuidC.text.trim(),
            'rssi_threshold': int.tryParse(threshC.text.trim()) ?? -70,
            'is_active': true,
          });
          Get.back();
        }
      }
    );
  }
}
