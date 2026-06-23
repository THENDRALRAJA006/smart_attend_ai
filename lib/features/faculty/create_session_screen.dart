import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'faculty_controller.dart';

class CreateSessionScreen extends StatefulWidget {
  const CreateSessionScreen({super.key});

  @override
  State<CreateSessionScreen> createState() => _CreateSessionScreenState();
}

class _CreateSessionScreenState extends State<CreateSessionScreen> {
  final FacultyController controller = Get.find<FacultyController>();
  int? selectedSubjectId;
  int? selectedClassroomId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Open Class Session'),
        centerTitle: true,
      ),
      body: Obx(() {
        if (controller.isLoading.value) {
          return const Center(child: CircularProgressIndicator(color: Color(0xFF6C63FF)));
        }

        if (controller.subjects.isEmpty || controller.classrooms.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.warning_amber_rounded, size: 48, color: Color(0xFFFFD600)),
                  const SizedBox(height: 12),
                  const Text(
                    'Missing Setup Metadata',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Ensure the administrator has loaded subjects and classrooms in the system database.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Color(0xFF94A3B8)),
                  ),
                  const SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: () => controller.checkActiveSession(),
                    child: const Text('RETRY LOADING'),
                  )
                ],
              ),
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Class Parameters',
                style: Get.textTheme.headlineMedium,
              ),
              const Text(
                'Choose the subject and classroom to establish BLE beacon advertising parameters.',
                style: TextStyle(color: Color(0xFF94A3B8)),
              ),
              const SizedBox(height: 32),

              // Subject Dropdown Selector
              Text('SELECT SUBJECT', style: TextStyle(color: const Color(0xFF94A3B8).withOpacity(0.8), fontSize: 11, letterSpacing: 1.0)),
              const SizedBox(height: 8),
              DropdownButtonFormField<int>(
                value: selectedSubjectId,
                hint: const Text('Choose subject...', style: TextStyle(color: Color(0xFF94A3B8))),
                items: controller.subjects.map<DropdownMenuItem<int>>((sub) {
                  return DropdownMenuItem<int>(
                    value: sub['id'],
                    child: Text('${sub['subject_name']} (${sub['subject_code']})'),
                  );
                }).toList(),
                onChanged: (val) {
                  setState(() {
                    selectedSubjectId = val;
                  });
                },
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.menu_book),
                ),
              ),
              const SizedBox(height: 24),

              // Classroom Dropdown Selector
              Text('SELECT CLASSROOM', style: TextStyle(color: const Color(0xFF94A3B8).withOpacity(0.8), fontSize: 11, letterSpacing: 1.0)),
              const SizedBox(height: 8),
              DropdownButtonFormField<int>(
                value: selectedClassroomId,
                hint: const Text('Choose classroom...', style: TextStyle(color: Color(0xFF94A3B8))),
                items: controller.classrooms.map<DropdownMenuItem<int>>((room) {
                  return DropdownMenuItem<int>(
                    value: room['id'],
                    child: Text('${room['room_name']} (${room['building'] ?? ''})'),
                  );
                }).toList(),
                onChanged: (val) {
                  setState(() {
                    selectedClassroomId = val;
                  });
                },
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.meeting_room),
                ),
              ),

              const Spacer(),

              // Submit trigger
              ElevatedButton.icon(
                onPressed: (selectedSubjectId != null && selectedClassroomId != null)
                    ? () => controller.createSession(selectedSubjectId!, selectedClassroomId!)
                    : null,
                icon: const Icon(Icons.play_arrow),
                label: const Text('START WINDOW'),
              ),
              const SizedBox(height: 12),
            ],
          ),
        );
      }),
    );
  }
}
