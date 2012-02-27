/*
 *   Capture an image from a webcam via /dev/video0 and write it to
 *  /var/www/shot.jpg
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdarg.h>
#include <errno.h>
#include <fcntl.h>
#include <time.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <X11/Xlib.h>
#include <Imlib2.h>
#include <giblib.h>
#include <sys/types.h>
#include <libv4l1-videodev.h>

#include "pwc-ioctl.h"



int grab_width     = 352;
int grab_height    = 288;
int cam_contrast   = 50;
int cam_brightness = 50;
int cam_hue        = 50;
int cam_colour     = 50;
int cam_whiteness  = 50;
int cam_framerate  = 30;
int device_palette = 0;
char *pwc_wb_mode  = "indoor";
int pwc_wb_red     = 50;
int pwc_wb_blue    = 50;
int verbose        = 0;


struct video_picture cam_pic;

/* these work for v4l only, not v4l2 */
int grab_input = 0;
int grab_norm = VIDEO_MODE_PAL;

/* drewp: removed static from these for use in cam.pyx */
struct video_mmap grab_buf;
int grab_fd = -1;
int grab_size = 0;
unsigned char *grab_data = NULL;


Imlib_Image convert_yuv420p_to_imlib2(unsigned char *mem,int width,int height);
int save_image(Imlib_Image image, char *file);

void
close_device()
{
  if (munmap(grab_data, grab_size) != 0) {
    perror("munmap()");
    exit(1);
  }
  grab_data = NULL;
  if (close(grab_fd))
    perror("close(grab_fd) ");
  grab_fd = -1;
}

int
try_palette(int fd,
            int pal,
            int depth)
{
  cam_pic.palette = pal;
  cam_pic.depth = depth;
  if (ioctl(fd, VIDIOCSPICT, &cam_pic) < 0)
    return 0;
  if (ioctl(fd, VIDIOCGPICT, &cam_pic) < 0)
    return 0;
  if (cam_pic.palette == pal)
    return 1;
  return 0;
}

int
find_palette(int fd,
             struct video_mmap *vid)
{
  if (try_palette(fd, VIDEO_PALETTE_RGB24, 24)) {
    if ( verbose ) {
      printf("negotiated palette RGB24\n");
    }
    return VIDEO_PALETTE_RGB24;
  }
  if (try_palette(fd, VIDEO_PALETTE_YUV420P, 16)) {
    if ( verbose ) {
      printf("negotiated palette YUV420P\n");
    }
    return VIDEO_PALETTE_YUV420P;
  }
  if (try_palette(fd, VIDEO_PALETTE_YUV420, 16)) {
    if ( verbose ) {
      printf("negotiated palette YUV420\n");
    }
    return VIDEO_PALETTE_YUV420;
  }
  fprintf(stderr, "No supported palette found.\n");
  exit(2);
  return 0;
}


void
grab_init(char *grab_device)
{
  struct video_capability grab_cap;
  struct video_channel grab_chan;
  struct video_mbuf vid_mbuf;
  int type;

  if ((grab_fd = open(grab_device, O_RDWR)) == -1) {
    fprintf(stderr, "open %s: %s\n", grab_device, strerror(errno));
    exit(1);
  }
  if (ioctl(grab_fd, VIDIOCGCAP, &grab_cap) == -1) {
    fprintf(stderr, "%s: no v4l device\n", grab_device);
    exit(1);
  }

  if (ioctl(grab_fd, VIDIOCGPICT, &cam_pic) < 0)
    perror("getting pic info");
  cam_pic.contrast = 65535 * ((float) cam_contrast / 100);
  cam_pic.brightness = 65535 * ((float) cam_brightness / 100);
  cam_pic.hue = 65535 * ((float) cam_hue / 100);
  cam_pic.colour = 65535 * ((float) cam_colour / 100);
  cam_pic.whiteness = 65535 * ((float) cam_whiteness / 100);
  if (ioctl(grab_fd, VIDIOCSPICT, &cam_pic) < 0)
    perror("setting cam pic");
  device_palette = find_palette(grab_fd, &grab_buf);

  grab_buf.format = device_palette;
  grab_buf.frame = 0;
  grab_buf.width = grab_width;
  grab_buf.height = grab_height;

  ioctl(grab_fd, VIDIOCGMBUF, &vid_mbuf);
  if ( verbose ) {
      printf("%s detected\n", grab_cap.name);
  }

  /* special philips features */
  if (sscanf(grab_cap.name, "Philips %d webcam", &type) > 0) {
    struct video_window vwin;
    int shutter = -1;
    int gain = -1;
    struct pwc_whitebalance wb;

    /* philips cam detected, maybe enable special features */
    if ( verbose ) {
      printf("enabling pwc-specific features\n");
    }

    ioctl(grab_fd, VIDIOCGWIN, &vwin);
    if (vwin.flags & PWC_FPS_MASK) {
      /* Set new framerate */
      vwin.flags &= ~PWC_FPS_FRMASK;
      vwin.flags |= (cam_framerate << PWC_FPS_SHIFT);
    }

    /* Turning off snapshot mode */
    vwin.flags &= ~(PWC_FPS_SNAPSHOT);

    if (ioctl(grab_fd, VIDIOCSWIN, &vwin) < 0)
      perror("trying to set extra pwc flags");

    if (ioctl(grab_fd, VIDIOCPWCSAGC, &gain) < 0)
      perror("trying to set gain");
    if (ioctl(grab_fd, VIDIOCPWCSSHUTTER, &shutter) < 0)
      perror("trying to set shutter");

    wb.mode = PWC_WB_AUTO;
    wb.manual_red = 50;
    wb.manual_blue = 50;
    if (!strcasecmp(pwc_wb_mode, "auto")) {
      wb.mode = PWC_WB_AUTO;
    } else if (!strcasecmp(pwc_wb_mode, "indoor")) {
      wb.mode = PWC_WB_INDOOR;
    } else if (!strcasecmp(pwc_wb_mode, "outdoor")) {
      wb.mode = PWC_WB_OUTDOOR;
    } else if (!strcasecmp(pwc_wb_mode, "fluorescent")) {
      wb.mode = PWC_WB_FL;
    } else if (!strcasecmp(pwc_wb_mode, "manual")) {
      wb.mode = PWC_WB_MANUAL;
      wb.manual_red = 65535 * ((float) pwc_wb_red / 100);
      wb.manual_blue = 65535 * ((float) pwc_wb_blue / 100);
    } else {
      printf("unknown pwc white balance mode '%s' ignored\n", pwc_wb_mode);
    }

    if (ioctl(grab_fd, VIDIOCPWCSAWB, &wb) < 0)
      perror("trying to set pwc white balance mode");
  }

  /* set image source and TV norm */
  grab_chan.channel = grab_input;
  if (ioctl(grab_fd, VIDIOCGCHAN, &grab_chan) == -1) {
    perror("ioctl VIDIOCGCHAN");
    exit(1);
  }
  grab_chan.channel = grab_input;
  grab_chan.norm = grab_norm;
  if (ioctl(grab_fd, VIDIOCSCHAN, &grab_chan) == -1) {
    perror("ioctl VIDIOCSCHAN");
    exit(1);
  }

  /*   grab_size = grab_buf.width * grab_buf.height * 3; */
  grab_size = vid_mbuf.size;
  grab_data =
    mmap(0, grab_size, PROT_READ | PROT_WRITE, MAP_SHARED, grab_fd, 0);
  if ((grab_data == NULL) || (-1 == (int) grab_data)) {
    fprintf(stderr,
            "couldn't mmap vidcam. your card doesn't support that?\n");
    exit(1);
  }
}

/* This is a really simplistic approach. Speedups are welcomed. */
Imlib_Image
convert_yuv420p_to_imlib2(unsigned char *src,
                          int width,
                          int height)
{
  int line, col;
  int y, u, v, yy, vr = 0, ug = 0, vg = 0, ub = 0;
  int r, g, b;
  unsigned char *sy, *su, *sv;
  Imlib_Image im;
  DATA32 *data, *dest;

  im = imlib_create_image(width, height);
  imlib_context_set_image(im);
  data = imlib_image_get_data();
  dest = data;

  sy = src;
  su = sy + (width * height);
  sv = su + (width * height / 4);

  for (line = 0; line < height; line++) {
    for (col = 0; col < width; col++) {
      y = *sy++;
      yy = y << 8;
      u = *su - 128;
      ug = 88 * u;
      ub = 454 * u;
      v = *sv - 128;
      vg = 183 * v;
      vr = 359 * v;

      if ((col & 1) == 0) {
        su++;
        sv++;
      }

      r = (yy + vr) >> 8;
      g = (yy - ug - vg) >> 8;
      b = (yy + ub) >> 8;

      if (r < 0)
        r = 0;
      if (r > 255)
        r = 255;
      if (g < 0)
        g = 0;
      if (g > 255)
        g = 255;
      if (b < 0)
        b = 0;
      if (b > 255)
        b = 255;

      *dest = (r << 16) | (g << 8) | b | 0xff000000;
      dest++;
    }
    if ((line & 1) == 0) {
      su -= width / 2;
      sv -= width / 2;
    }
  }
  imlib_image_put_back_data(data);
  return im;
}

/* This is a really simplistic approach. Speedups are welcomed. */
Imlib_Image
convert_yuv420i_to_imlib2(unsigned char *src,
                          int width,
                          int height)
{
  int line, col, linewidth;
  int y, u, v, yy, vr = 0, ug = 0, vg = 0, ub = 0;
  int r, g, b;
  unsigned char *sy, *su, *sv;
  Imlib_Image im;
  DATA32 *data, *dest;

  im = imlib_create_image(width, height);
  imlib_context_set_image(im);
  data = imlib_image_get_data();
  dest = data;

  linewidth = width + (width >> 1);
  sy = src;
  su = sy + 4;
  sv = su + linewidth;

  /* 
     The biggest problem is the interlaced data, and the fact that odd
     add even lines have V and U data, resp. 
   */

  for (line = 0; line < height; line++) {
    for (col = 0; col < width; col++) {
      y = *sy++;
      yy = y << 8;
      if ((col & 1) == 0) {
        /* only at even colums we update the u/v data */
        u = *su - 128;
        ug = 88 * u;
        ub = 454 * u;
        v = *sv - 128;
        vg = 183 * v;
        vr = 359 * v;

        su++;
        sv++;
      }
      if ((col & 3) == 3) {
        sy += 2;        /* skip u/v */
        su += 4;        /* skip y */
        sv += 4;        /* skip y */
      }
      r = (yy + vr) >> 8;
      g = (yy - ug - vg) >> 8;
      b = (yy + ub) >> 8;

      if (r < 0)
        r = 0;
      if (r > 255)
        r = 255;
      if (g < 0)
        g = 0;
      if (g > 255)
        g = 255;
      if (b < 0)
        b = 0;
      if (b > 255)
        b = 255;

      *dest = (r << 16) | (g << 8) | b | 0xff000000;
      dest++;
    }
    if (line & 1) {
      su += linewidth;
      sv += linewidth;
    } else {
      su -= linewidth;
      sv -= linewidth;
    }
  }
  imlib_image_put_back_data(data);
  return im;
}

Imlib_Image
convert_rgb24_to_imlib2(unsigned char *mem,
                        int width,
                        int height)
{
  Imlib_Image im;
  DATA32 *data, *dest;
  unsigned char *src;
  int i;

  im = imlib_create_image(width, height);
  imlib_context_set_image(im);
  data = imlib_image_get_data();

  dest = data;
  src = mem;
  i = width * height;
  while (i--) {
    *dest = (src[2] << 16) | (src[1] << 8) | src[0] | 0xff000000;
    dest++;
    src += 3;
  }

  imlib_image_put_back_data(data);

  return im;
}


Imlib_Image
grab_one(int *width,
         int *height)
{
  Imlib_Image im;
  int i = 0;
  int j = 5;

  if (grab_fd == -1)
    {
      printf("Error in grab_one - not initialized\n" );
      exit(3);
    }
//    grab_init();

  if (j == 0)
    j++;

  while (j--) {
    if (ioctl(grab_fd, VIDIOCMCAPTURE, &grab_buf) == -1) {
      perror("ioctl VIDIOCMCAPTURE");
      return NULL;
    }
    if (ioctl(grab_fd, VIDIOCSYNC, &i) == -1) {
      perror("ioctl VIDIOCSYNC");
      return NULL;
    }
  }
  switch (device_palette) {
    case VIDEO_PALETTE_YUV420P:
      im =
        convert_yuv420p_to_imlib2(grab_data, grab_buf.width, grab_buf.height);
      break;
    case VIDEO_PALETTE_YUV420:
      im =
        convert_yuv420i_to_imlib2(grab_data, grab_buf.width, grab_buf.height);
      break;
    case VIDEO_PALETTE_RGB24:
      im =
        convert_rgb24_to_imlib2(grab_data, grab_buf.width, grab_buf.height);
      break;
    default:
      fprintf(stderr, "eeek");
      exit(2);
  }

  close_device();
  if (im) {
    imlib_context_set_image(im);
//    imlib_image_attach_data_value("quality", NULL, grab_quality, NULL);
  }
  *width = grab_buf.width;
  *height = grab_buf.height;
  return im;
}


/* ---------------------------------------------------------------------- */


int
save_image(Imlib_Image image,
           char *file)
{
  Imlib_Load_Error err;

  gib_imlib_save_image_with_error_return(image, file, &err);
  if ((err) || (!image)) {
    switch (err) {
      case IMLIB_LOAD_ERROR_FILE_DOES_NOT_EXIST:
        printf("Error saving image %s - File does not exist", file);
        break;
      case IMLIB_LOAD_ERROR_FILE_IS_DIRECTORY:
        printf("Error saving image %s - Directory specified for image filename",
            file);
        break;
      case IMLIB_LOAD_ERROR_PERMISSION_DENIED_TO_READ:
        printf("Error saving image %s - No read access to directory", file);
        break;
      case IMLIB_LOAD_ERROR_UNKNOWN:
      case IMLIB_LOAD_ERROR_NO_LOADER_FOR_FILE_FORMAT:
        printf("Error saving image %s - No Imlib2 loader for that file format",
            file);
        break;
      case IMLIB_LOAD_ERROR_PATH_TOO_LONG:
        printf("Error saving image %s - Path specified is too long", file);
        break;
      case IMLIB_LOAD_ERROR_PATH_COMPONENT_NON_EXISTANT:
        printf("Error saving image %s - Path component does not exist", file);
        break;
      case IMLIB_LOAD_ERROR_PATH_COMPONENT_NOT_DIRECTORY:
        printf("Error saving image %s - Path component is not a directory",
            file);
        break;
      case IMLIB_LOAD_ERROR_PATH_POINTS_OUTSIDE_ADDRESS_SPACE:
        printf("Error saving image %s - Path points outside address space",
            file);
        break;
      case IMLIB_LOAD_ERROR_TOO_MANY_SYMBOLIC_LINKS:
        printf("Error saving image %s - Too many levels of symbolic links",
            file);
        break;
      case IMLIB_LOAD_ERROR_OUT_OF_MEMORY:
        printf("Error saving image %s - Out of memory", file);
        break;
      case IMLIB_LOAD_ERROR_OUT_OF_FILE_DESCRIPTORS:
        gib_eprintf("While loading %s - Out of file descriptors", file);
        break;
      case IMLIB_LOAD_ERROR_PERMISSION_DENIED_TO_WRITE:
        printf("Error saving image %s - Cannot write to directory", file);
        break;
      case IMLIB_LOAD_ERROR_OUT_OF_DISK_SPACE:
        printf("Error saving image %s - Cannot write - out of disk space", file);
        break;
      default:
        printf
          ("Error saving image %s - Unknown error (%d). Attempting to continue",
           file, err);
        break;
    }
    return 0;
  } else {
    if ( verbose ) {
      printf("Saved image to %s\n", file );
    }
  }
  return 1;
}


int
main(int argc,
     char *argv[])
{
  Imlib_Image image;
  int width, height;

  char *fileName = "shot.jpg";
  char *device   = "/dev/video0";
  int i;

  for( i = 1; i < argc; i++ )
  {
    if ( strcmp( argv[i], "-version" ) == 0 ) {
      printf("camgrab v0.1 - by Steve Kemp\n");
      return(0);
    }
    if ( strcmp( argv[i], "-help" ) == 0 ) {
      printf("camgrab v0.1 - by Steve Kemp\n");
      printf("\nUsage: camgrab [options]\n" );
      printf("\n Where options include:\n");
      printf("\t-device dev\tSpecify the device to capture from.\n" );
      printf("\t-help\tShow this help.\n");
      printf("\t-output file\tSpecify the output file to save the image to.\n");
      printf("\t-verbose\tIncrease diagnostics.\n");
      printf("\t-version\tDisplay the version of this application.\n\n");
      return(0);
    }
    if ( strcmp( argv[i], "-verbose" ) == 0 ) {
      verbose = 1;
      printf("Verbose enabled.\n");
    }
    if ( strcmp( argv[i], "-device" ) == 0 ) {
      if ( i+1 < argc ) {
	device = argv[i+1];
	i++;
      } else {
	printf("-device requires an argument.\n" );
	exit( -1 );
      }
    }
    if ( strcmp( argv[i], "-output" ) == 0 ) {
      if ( i+1 < argc ) {
	fileName = argv[i+1];
	i++;
      } else {
	printf("-output requires an argument.\n" );
	exit( -1 );
      }
    }
  }
  imlib_context_set_direction(IMLIB_TEXT_TO_RIGHT);
  imlib_context_set_operation(IMLIB_OP_COPY);
  imlib_set_cache_size(0);

  /* init everything */
  grab_init(device);

  /* Grab an image */
  image = grab_one(&width, &height);

  /* Save */
  imlib_context_set_image(image);
  save_image(image, fileName);
  gib_imlib_free_image_and_decache(image);

  /* Exit */
  return 0;
}
